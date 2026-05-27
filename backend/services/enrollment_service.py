try:
    from constants import ENROLLMENT_REOPENABLE_STATUSES, ENROLLMENT_TYPE_SINGLE, PAYMENT_OPTION_FULL
    from models import Enrollment
    from services.credit_service import available_credit_for_user_activity, consume_credit_for_enrollment
    from services.payment_service import (
        class_has_finished,
        enrollment_payment_quote,
        expire_payment_for_enrollment,
        has_approved_payment,
        payment_expires_at,
        payment_type_for_enrollment,
        recompute_enrollment_payment_state,
    )
except ModuleNotFoundError:
    from ..constants import ENROLLMENT_REOPENABLE_STATUSES, ENROLLMENT_TYPE_SINGLE, PAYMENT_OPTION_FULL
    from ..models import Enrollment
    from .credit_service import available_credit_for_user_activity, consume_credit_for_enrollment
    from .payment_service import (
        class_has_finished,
        enrollment_payment_quote,
        expire_payment_for_enrollment,
        has_approved_payment,
        payment_expires_at,
        payment_type_for_enrollment,
        recompute_enrollment_payment_state,
    )


def class_capacity(class_obj):
    return class_obj.cupoMaximo if class_obj and class_obj.cupoMaximo is not None else 20


def validate_class_available_for_enrollment(class_obj, current_dt):
    if not class_obj:
        return "Clase no encontrada", 404
    if getattr(class_obj, "estado", class_obj.STATUS_ACTIVE) != class_obj.STATUS_ACTIVE:
        return "La clase no está disponible para inscripción", 400
    if class_has_finished(class_obj, current_dt):
        return "No se puede inscribir a una clase que ya comenzó", 400
    return None, None


def expire_enrollment_if_needed(enrollment, current_dt=None):
    if not enrollment or enrollment.estado != Enrollment.STATUS_PENDING_PAYMENT:
        return False

    if class_has_finished(enrollment.class_, current_dt):
        enrollment.estado = Enrollment.STATUS_EXPIRED
        expire_payment_for_enrollment(enrollment, current_dt)
        return True
    return False


def restore_future_expired_enrollment_if_needed(enrollment, current_dt=None):
    try:
        from services.datetime_service import current_datetime, datetime_in_app_timezone
    except ModuleNotFoundError:
        from .datetime_service import current_datetime, datetime_in_app_timezone

    if not enrollment or has_approved_payment(enrollment):
        return False
    if class_has_finished(enrollment.class_, current_dt):
        return False

    current_dt = datetime_in_app_timezone(current_dt or current_datetime())
    changed = False
    if enrollment.estado == Enrollment.STATUS_EXPIRED:
        enrollment.estado = Enrollment.STATUS_PENDING_PAYMENT
        changed = True

    for payment in list(getattr(enrollment, "payments", []) or []):
        if payment.status == payment.STATUS_EXPIRED:
            payment.status = payment.STATUS_PENDING
            payment_created_at = datetime_in_app_timezone(payment.created_at)
            if payment_created_at and payment_created_at > current_dt:
                payment.created_at = current_dt.replace(tzinfo=None)
            changed = True

    return changed


def validate_enrollment_payable(enrollment, current_user, current_dt):
    if not enrollment or enrollment.user_id != current_user.id:
        return "Inscripción no encontrada", 404

    class_obj = enrollment.class_
    if not class_obj:
        return "Clase no encontrada", 404
    if class_has_finished(class_obj, current_dt):
        if enrollment.estado == Enrollment.STATUS_PENDING_PAYMENT:
            enrollment.estado = Enrollment.STATUS_EXPIRED
            expire_payment_for_enrollment(enrollment, current_dt)
        return "No se puede pagar una clase ya finalizada", 400
    if enrollment.estado != Enrollment.STATUS_PENDING_PAYMENT:
        return "La inscripción no está pendiente de pago", 400
    if has_approved_payment(enrollment):
        enrollment.estado = Enrollment.STATUS_PAID
        return "La inscripción ya tiene un pago aprobado", 409
    return None, None


def enrollment_payload(enrollment, current_dt=None):
    recompute_enrollment_payment_state(enrollment, current_dt)
    class_obj = enrollment.class_
    quote = enrollment_payment_quote(enrollment, current_dt)
    expires_at = payment_expires_at(class_obj)
    return {
        "id": enrollment.id,
        "user_id": enrollment.user_id,
        "class_id": enrollment.class_id,
        "class_name": class_obj.name if class_obj else None,
        "actividad": class_obj.actividad.name if class_obj and class_obj.actividad else None,
        "fecha_hora": class_obj.fecha_hora.isoformat() if class_obj and class_obj.fecha_hora else None,
        "estado": enrollment.estado,
        "tipo": enrollment.tipo,
        "expires_at": expires_at.isoformat() if expires_at else None,
        "product_type": payment_type_for_enrollment(enrollment),
        "payment_type": payment_type_for_enrollment(enrollment),
        "payment_option": PAYMENT_OPTION_FULL,
        "amount": quote["amount"],
        "discount_percentage": quote["discount_percentage"],
        "final_amount": quote["final_amount"],
        "total_amount": enrollment.total_amount,
        "paid_amount": enrollment.paid_amount,
        "remaining_amount": enrollment.remaining_amount,
        "payment_status": enrollment.payment_status,
        "is_payable": (
            enrollment.estado == Enrollment.STATUS_PENDING_PAYMENT
            and not class_has_finished(class_obj, current_dt)
        ),
    }


def credit_enrollment_payload(enrollment, credit, current_dt=None):
    return {
        "message": "Inscripción realizada utilizando crédito",
        "credit_used": True,
        "credit_id": credit.id,
        "enrollment": enrollment_payload(enrollment, current_dt),
    }


def create_or_reopen_enrollment(current_user, class_obj, tipo, enrollment_map, current_dt):
    enrollment = Enrollment.query.filter_by(user_id=current_user.id, class_id=class_obj.id).first()
    capacity = class_capacity(class_obj)

    if enrollment:
        expire_enrollment_if_needed(enrollment, current_dt)
        if enrollment.estado == Enrollment.STATUS_PAID or has_approved_payment(enrollment):
            enrollment.estado = Enrollment.STATUS_PAID
            return enrollment, "already_paid"

        if enrollment.estado == Enrollment.STATUS_PENDING_PAYMENT:
            credit = available_credit_for_user_activity(current_user.id, class_obj.id_actividad, current_dt)
            if credit:
                consume_credit_for_enrollment(credit, enrollment, current_dt)
                enrollment._used_credit = credit
                return enrollment, "credit_used"
            return enrollment, "already_pending"

        if enrollment.estado in ENROLLMENT_REOPENABLE_STATUSES:
            if enrollment_map.get(class_obj.id, 0) >= capacity:
                return enrollment, "full"
            enrollment.estado = Enrollment.STATUS_PENDING_PAYMENT
            enrollment.requiere_reembolso = False
            enrollment.tipo = tipo or enrollment.tipo or ENROLLMENT_TYPE_SINGLE
            return enrollment, "created"

    if enrollment_map.get(class_obj.id, 0) >= capacity:
        return None, "full"

    enrollment = Enrollment(
        user_id=current_user.id,
        class_id=class_obj.id,
        tipo=tipo or ENROLLMENT_TYPE_SINGLE,
        estado=Enrollment.STATUS_PENDING_PAYMENT,
    )
    return enrollment, "new"
