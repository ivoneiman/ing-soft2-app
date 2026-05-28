import logging
from datetime import timedelta

try:
    from constants import (
        CREDIT_API_STATUS_AVAILABLE,
        CREDIT_API_STATUS_EXPIRED,
        CREDIT_API_STATUS_USED,
        CREDIT_EXPIRATION_DAYS,
        CREDIT_STATUS_AVAILABLE,
        CREDIT_STATUS_USED,
        PAYMENT_METHOD_CREDIT,
        PAYMENT_STATUS_APPROVED,
    )
    from models import Credit, Payment, db
    from services.datetime_service import current_datetime, datetime_in_app_timezone
    from services.payment_service import payment_type_for_enrollment, recompute_enrollment_payment_state
except ModuleNotFoundError:
    from ..constants import (
        CREDIT_API_STATUS_AVAILABLE,
        CREDIT_API_STATUS_EXPIRED,
        CREDIT_API_STATUS_USED,
        CREDIT_EXPIRATION_DAYS,
        CREDIT_STATUS_AVAILABLE,
        CREDIT_STATUS_USED,
        PAYMENT_METHOD_CREDIT,
        PAYMENT_STATUS_APPROVED,
    )
    from ..models import Credit, Payment, db
    from .datetime_service import current_datetime, datetime_in_app_timezone
    from .payment_service import payment_type_for_enrollment, recompute_enrollment_payment_state

logger = logging.getLogger(__name__)


def credit_expiration_from(current_dt=None):
    current_dt = datetime_in_app_timezone(current_dt or current_datetime())
    return (current_dt + timedelta(days=CREDIT_EXPIRATION_DAYS)).replace(tzinfo=None)


def is_credit_valid(credit, activity_id, current_dt=None):
    if not credit or credit.activity_id != activity_id or credit.used:
        return False

    expires_at = datetime_in_app_timezone(credit.expires_at)
    current_dt = datetime_in_app_timezone(current_dt or current_datetime())
    return bool(expires_at and expires_at > current_dt)


def available_credit_for_user_activity(user_id, activity_id, current_dt=None):
    credits = (
        Credit.query
        .filter_by(user_id=user_id, activity_id=activity_id, used=False)
        .order_by(Credit.expires_at.asc(), Credit.id.asc())
        .all()
    )
    for credit in credits:
        if is_credit_valid(credit, activity_id, current_dt):
            return credit
    return None


def consume_credit_for_enrollment(credit, enrollment, current_dt=None):
    class_obj = getattr(enrollment, "class_", None)
    if not class_obj or not is_credit_valid(credit, class_obj.id_actividad, current_dt):
        logger.warning(
            "[Credits] credito_invalido credit_id=%s enrollment_id=%s",
            getattr(credit, "id", None),
            getattr(enrollment, "id", None),
        )
        return False

    current_dt = current_dt or current_datetime()
    credit.used = True
    credit.used_at = datetime_in_app_timezone(current_dt).replace(tzinfo=None)
    credit.estado = CREDIT_STATUS_USED
    enrollment.estado = enrollment.STATUS_PAID
    enrollment.requiere_reembolso = False

    payment = Payment(
        user_id=enrollment.user_id,
        enrollment_id=enrollment.id,
        class_id=enrollment.class_id,
        product_type=payment_type_for_enrollment(enrollment),
        payment_type=Payment.TYPE_FULL,
        payment_method=PAYMENT_METHOD_CREDIT,
        amount=0,
        discount_percentage=0,
        final_amount=0,
        status=PAYMENT_STATUS_APPROVED,
    )
    db.session.add(payment)
    db.session.flush()
    db.session.expire(enrollment, ["payments"])
    recompute_enrollment_payment_state(enrollment, current_dt)
    logger.info(
        "[Credits] consumido credit_id=%s user_id=%s enrollment_id=%s",
        credit.id,
        enrollment.user_id,
        enrollment.id,
    )
    return True


def credit_exists_for_cancelled_enrollment(enrollment, class_obj):
    query = Credit.query.filter_by(
        user_id=enrollment.user_id,
        activity_id=class_obj.id_actividad,
        origin_class_id=class_obj.id,
    )
    if not enrollment.id:
        return query.first() is not None

    return (
        query.filter(Credit.enrollment_id == enrollment.id).first() is not None
        or query.filter(Credit.enrollment_id.is_(None)).first() is not None
    )


def generate_credit_for_paid_enrollment(enrollment, class_obj, current_dt=None):
    try:
        from services.payment_service import has_approved_payment
    except ModuleNotFoundError:
        from .payment_service import has_approved_payment

    if not (enrollment.estado == enrollment.STATUS_PAID or has_approved_payment(enrollment)):
        return None
    if credit_exists_for_cancelled_enrollment(enrollment, class_obj):
        logger.info(
            "[Credits] duplicado enrollment_id=%s class_id=%s",
            enrollment.id,
            class_obj.id,
        )
        return None

    credit = Credit(
        user_id=enrollment.user_id,
        activity_id=class_obj.id_actividad,
        origin_class_id=class_obj.id,
        enrollment_id=enrollment.id,
        expires_at=credit_expiration_from(current_dt),
        used=False,
        estado=CREDIT_STATUS_AVAILABLE,
    )
    db.session.add(credit)
    logger.info(
        "[Credits] creado user_id=%s activity_id=%s enrollment_id=%s",
        enrollment.user_id,
        class_obj.id_actividad,
        enrollment.id,
    )
    return credit


def credit_payload(credit, current_dt=None):
    item = credit.to_dict()
    if credit.used:
        item["status"] = CREDIT_API_STATUS_USED
    elif not is_credit_valid(credit, credit.activity_id, current_dt):
        item["status"] = CREDIT_API_STATUS_EXPIRED
        item["estado"] = "Vencido"
    else:
        item["status"] = CREDIT_API_STATUS_AVAILABLE
        item["estado"] = CREDIT_STATUS_AVAILABLE
    return item
