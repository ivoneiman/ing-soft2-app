import logging
import os
from calendar import monthrange
from decimal import Decimal, ROUND_HALF_UP
from datetime import timedelta
from urllib.parse import quote

try:
    from constants import (
        DISCOUNT_PERCENTAGES,
        DISCOUNT_PERIODS,
        ENROLLMENT_TYPE_MONTHLY,
        PAYMENT_METHOD_MERCADO_PAGO,
        PAYMENT_OPTION_DEPOSIT,
        PAYMENT_OPTION_FULL,
        PAYMENT_STATUS_APPROVED,
        PAYMENT_STATUS_EXPIRED,
        PAYMENT_STATUS_PENDING,
        PAYMENT_TYPE_INDIVIDUAL_CLASS,
        PAYMENT_TYPE_MONTHLY_SUBSCRIPTION,
    )
    from models import Payment, db
    from services.datetime_service import current_datetime, datetime_in_app_timezone
except ModuleNotFoundError:
    from ..constants import (
        DISCOUNT_PERCENTAGES,
        DISCOUNT_PERIODS,
        ENROLLMENT_TYPE_MONTHLY,
        PAYMENT_METHOD_MERCADO_PAGO,
        PAYMENT_OPTION_DEPOSIT,
        PAYMENT_OPTION_FULL,
        PAYMENT_STATUS_APPROVED,
        PAYMENT_STATUS_EXPIRED,
        PAYMENT_STATUS_PENDING,
        PAYMENT_TYPE_INDIVIDUAL_CLASS,
        PAYMENT_TYPE_MONTHLY_SUBSCRIPTION,
    )
    from ..models import Payment, db
    from .datetime_service import current_datetime, datetime_in_app_timezone

logger = logging.getLogger(__name__)


def configured_amount(name, default):
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return float(default)


def current_discount_period_percentage(current_dt=None):
    current_dt = current_dt or current_datetime()
    today = current_dt.day
    last_day = monthrange(current_dt.year, current_dt.month)[1]

    for period in DISCOUNT_PERIODS:
        end_day = period["end_day"] or last_day
        if period["start_day"] <= today <= end_day:
            return period["percentage"]
    return 0


def discount_rules_payload(current_dt=None):
    current_dt = current_dt or current_datetime()
    last_day = monthrange(current_dt.year, current_dt.month)[1]
    return {
        "current_percentage": current_discount_period_percentage(current_dt),
        "allowed_percentages": list(DISCOUNT_PERCENTAGES),
        "periods": [
            {
                "percentage": period["percentage"],
                "start_day": period["start_day"],
                "end_day": period["end_day"] or last_day,
            }
            for period in DISCOUNT_PERIODS
        ],
    }


def class_has_finished(class_obj, current_dt=None):
    class_datetime = datetime_in_app_timezone(class_obj.fecha_hora if class_obj else None)
    if not class_datetime:
        return False

    current_dt = datetime_in_app_timezone(current_dt or current_datetime())
    return class_datetime <= current_dt


def payment_expires_at(class_obj):
    if not class_obj or not class_obj.fecha_hora:
        return None
    return class_obj.fecha_hora - timedelta(minutes=1)


def payment_amount(payment_type, payment_option):
    if payment_type == PAYMENT_TYPE_MONTHLY_SUBSCRIPTION:
        return configured_amount("PAYMENT_MONTHLY_AMOUNT", 10000)

    amount = configured_amount("PAYMENT_CLASS_AMOUNT", 3000)
    if payment_option == PAYMENT_OPTION_DEPOSIT:
        deposit_percentage = configured_amount("PAYMENT_DEPOSIT_PERCENTAGE", 50)
        return amount * (deposit_percentage / 100)
    return amount


def calculate_final_amount(amount, discount_percentage):
    original_amount = Decimal(str(amount))
    discount = Decimal(str(discount_percentage))
    final_amount = original_amount - (original_amount * discount / Decimal("100"))
    return float(final_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def payment_quote(payment_type, payment_option=PAYMENT_OPTION_FULL, current_dt=None):
    amount = payment_amount(payment_type, payment_option)
    discount_percentage = current_discount_period_percentage(current_dt)
    return {
        "amount": amount,
        "discount_percentage": discount_percentage,
        "final_amount": calculate_final_amount(amount, discount_percentage),
    }


def payment_type_for_enrollment(enrollment):
    return (
        PAYMENT_TYPE_MONTHLY_SUBSCRIPTION
        if getattr(enrollment, "tipo", None) == ENROLLMENT_TYPE_MONTHLY
        else PAYMENT_TYPE_INDIVIDUAL_CLASS
    )


def has_approved_payment(enrollment):
    return any(
        payment.status == PAYMENT_STATUS_APPROVED
        for payment in getattr(enrollment, "payments", [])
    )


def enrollment_payment_quote(enrollment, current_dt=None):
    return payment_quote(payment_type_for_enrollment(enrollment), PAYMENT_OPTION_FULL, current_dt)


def expire_payment_for_enrollment(enrollment, current_dt=None):
    if not enrollment or has_approved_payment(enrollment):
        return False
    if not class_has_finished(enrollment.class_, current_dt):
        return False

    changed = False
    has_expired_payment = False
    payments = list(getattr(enrollment, "payments", []) or [])

    for payment in payments:
        if payment.status == PAYMENT_STATUS_EXPIRED:
            has_expired_payment = True
        elif payment.status == PAYMENT_STATUS_PENDING:
            payment.status = PAYMENT_STATUS_EXPIRED
            has_expired_payment = True
            changed = True

    if not has_expired_payment:
        quote_data = enrollment_payment_quote(enrollment, current_dt)
        db.session.add(Payment(
            user_id=enrollment.user_id,
            enrollment_id=enrollment.id,
            class_id=enrollment.class_id,
            payment_type=payment_type_for_enrollment(enrollment),
            payment_method=PAYMENT_METHOD_MERCADO_PAGO,
            amount=quote_data["amount"],
            discount_percentage=quote_data["discount_percentage"],
            final_amount=quote_data["final_amount"],
            status=PAYMENT_STATUS_EXPIRED,
            created_at=payment_expires_at(enrollment.class_) or current_dt,
        ))
        changed = True

    return changed


def enrollment_has_other_approved_payment(payment):
    if not payment or not payment.enrollment_id:
        return False

    return (
        Payment.query
        .filter(
            Payment.enrollment_id == payment.enrollment_id,
            Payment.id != payment.id,
            Payment.status == PAYMENT_STATUS_APPROVED,
        )
        .first()
        is not None
    )


def log_discount_quote(current_dt, class_obj, discount_percentage, amount, final_amount):
    class_datetime = datetime_in_app_timezone(class_obj.fecha_hora if class_obj else None)
    logger.info(
        "[Discount] today=%s class_datetime=%s discount=%s original_amount=%s final_amount=%s",
        current_dt.date().isoformat(),
        class_datetime.isoformat() if class_datetime else None,
        discount_percentage,
        amount,
        final_amount,
    )


def payment_error_message(status_detail):
    if status_detail == "cc_rejected_insufficient_amount":
        return "Fondos insuficientes"
    if status_detail and status_detail.startswith("cc_rejected"):
        return "Pago rechazado"
    return "Error del servidor de pagos"


def frontend_payments_url(status, message=None):
    url = f"{os.getenv('FRONTEND_PAYMENTS_URL', 'http://localhost:5173/pagos')}?status={status}"
    if message:
        url = f"{url}&message={quote(message)}"
    return url


def configured_url(name, default):
    value = os.getenv(name)
    return value.strip() if value and value.strip() else default


def is_absolute_http_url(value):
    return isinstance(value, str) and value.strip().startswith(("http://", "https://"))


def validate_mercado_pago_back_urls(preference_data):
    if "back_url" in preference_data:
        return "back_urls debe llamarse en plural"
    if "back_urls" not in preference_data:
        return "back_urls debe estar definido como objeto"

    back_urls = preference_data.get("back_urls")
    if not isinstance(back_urls, dict):
        return "back_urls debe estar definido como objeto"
    if "auto_return" in back_urls:
        return "auto_return debe estar al mismo nivel que back_urls"

    for key in ["success", "failure", "pending"]:
        value = back_urls.get(key)
        if not value:
            return f"back_urls.{key} debe estar definido"
        if not isinstance(value, str):
            return f"back_urls.{key} debe ser un string"
        if not value.strip():
            return f"back_urls.{key} no puede estar vacío"
        if not is_absolute_http_url(value):
            return f"back_urls.{key} debe ser una URL absoluta http:// o https://"

    if preference_data.get("auto_return") == "approved" and not is_absolute_http_url(back_urls.get("success")):
        return "auto_return approved requiere back_urls.success válido"
    if "auto_return" not in preference_data:
        return "auto_return debe estar definido como approved"
    if preference_data.get("auto_return") != "approved":
        return "auto_return debe estar definido como approved"
    return None


def log_mercado_pago_payload(preference_data):
    logger.info("[MercadoPago] payload=%s", preference_data)


def log_mercado_pago_response(preference_result):
    if isinstance(preference_result, dict):
        logger.info(
            "[MercadoPago] status=%s response=%s",
            preference_result.get("status"),
            preference_result.get("response"),
        )
    else:
        logger.info("[MercadoPago] response=%s", preference_result)


def mercado_pago_checkout_url(preference_response):
    checkout_mode = os.getenv("MERCADOPAGO_CHECKOUT_MODE", os.getenv("ENVIRONMENT", "")).lower()
    if checkout_mode in ["sandbox", "development", "dev"]:
        return preference_response.get("sandbox_init_point") or preference_response.get("init_point")
    return preference_response.get("init_point") or preference_response.get("sandbox_init_point")
