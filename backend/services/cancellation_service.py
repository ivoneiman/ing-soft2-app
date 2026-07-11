import logging

try:
    from models import Enrollment, db
    from constants import ENROLLMENT_TYPE_MONTHLY
    from services.payment_service import (
        class_has_finished,
        expire_pending_payments_for_enrollment,
        has_approved_payment,
        recompute_enrollment_payment_state,
    )
    from services.credit_service import generate_credit_for_paid_enrollment
    from services.enrollment_service import enrollment_is_cancelable
except ModuleNotFoundError:
    from ..models import Enrollment, db
    from ..constants import ENROLLMENT_TYPE_MONTHLY
    from .payment_service import (
        class_has_finished,
        expire_pending_payments_for_enrollment,
        has_approved_payment,
        recompute_enrollment_payment_state,
    )
    from .credit_service import generate_credit_for_paid_enrollment
    from .enrollment_service import enrollment_is_cancelable

logger = logging.getLogger(__name__)


def cancel_class(class_obj, current_dt):
    class_obj.estado = class_obj.STATUS_CANCELLED
    enrollments = Enrollment.query.filter_by(class_id=class_obj.id).all()

    credits_created = 0
    email_jobs = []
    for enrollment in enrollments:
        credit = generate_credit_for_paid_enrollment(enrollment, class_obj, current_dt)
        credited = credit is not None
        if credited:
            credits_created += 1

        if enrollment.estado != Enrollment.STATUS_CANCELLED:
            enrollment.estado = Enrollment.STATUS_CANCELLED

        email_jobs.append((enrollment.user, class_obj, credit))

    logger.info(
        "[Cancelaciones] class_id=%s enrollments=%s credits=%s",
        class_obj.id,
        len(enrollments),
        credits_created,
    )
    return {
        "credits_created": credits_created,
        "email_jobs": email_jobs,
    }


def cancel_enrollment(enrollment, current_user, current_dt, skip_credit_generation=False):
    if not enrollment:
        return None, "Inscripción no encontrada", 404
    if enrollment.user_id != current_user.id and current_user.role not in ["admin", "employee"]:
        return None, "No tenés permisos para cancelar esta inscripción", 403
    if enrollment.estado == Enrollment.STATUS_CANCELLED:
        return None, "Esta inscripción ya fue cancelada", 400

    class_obj = enrollment.class_
    if not class_obj:
        return None, "Clase asociada no encontrada", 404
    if class_has_finished(class_obj, current_dt):
        return None, "No se puede cancelar una clase ya iniciada", 400
    if not enrollment_is_cancelable(enrollment, current_dt):
        return None, "La inscripción solo puede cancelarse hasta 24 horas antes del inicio de la clase", 400

    recompute_enrollment_payment_state(enrollment, current_dt)
    # Los créditos reutilizables sólo existen para bajas dentro de una suscripción mensual;
    # las clases individuales no generan crédito (ver mensaje de baja simulando un reembolso).
    should_generate_credit = (
        not skip_credit_generation
        and enrollment.tipo == ENROLLMENT_TYPE_MONTHLY
        and has_approved_payment(enrollment)
    )

    credit = None
    if should_generate_credit:
        # Regla de negocio: el modelo actual de créditos representa reservas reutilizables,
        # no dinero. Por eso una seña aprobada genera un crédito completo, sin prorrateo.
        credit = generate_credit_for_paid_enrollment(enrollment, class_obj, current_dt)

    expired_payments = expire_pending_payments_for_enrollment(enrollment)
    enrollment.estado = Enrollment.STATUS_CANCELLED

    logger.info(
        "[Cancelaciones] enrollment_id=%s user_id=%s credit_generated=%s pending_expired=%s",
        enrollment.id,
        enrollment.user_id,
        credit is not None,
        expired_payments,
    )
    return {
        "enrollment": enrollment,
        "class": class_obj,
        "credit": credit,
        "credit_generated": credit is not None,
        "pending_payments_expired": expired_payments,
    }, None, None
