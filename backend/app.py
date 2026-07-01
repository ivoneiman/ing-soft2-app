import os
import logging
import re
import random
import time
import threading
import urllib.parse
from datetime import datetime, timedelta
from calendar import monthrange
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from dotenv import load_dotenv

from flask import Flask, request, jsonify, session, redirect, g, has_request_context
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import case, event, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.engine import Engine

try:
    from email_service import (
        send_admin_login_code,
        send_class_cancelled_email,
        send_credit_generated_email,
        send_waitlist_promotion_email,
    )
    from mercadopago_config import get_mercadopago_client
    from models import db, User
    # Importar todos los modelos requeridos
    from models import Class, Enrollment, Attendance, Actividades, Credit, Credito, Notification, Payment, SystemSetting, WaitlistEntry
    from constants import (
        DISCOUNT_PERCENTAGES,
        ENROLLMENT_STATUS_PENDING_PAYMENT,
        ENROLLMENT_TYPE_SINGLE,
        ENROLLMENT_TYPE_MONTHLY,
        WAITLIST_TYPE_INDIVIDUAL,
        WAITLIST_TYPE_MONTHLY,
        ENROLLMENT_PAYMENT_STATUS_EXPIRED,
        ENROLLMENT_PAYMENT_STATUS_PAID,
        ENROLLMENT_PAYMENT_STATUS_PENDING,
        PAYMENT_PRODUCT_TYPE_INDIVIDUAL_CLASS,
        PAYMENT_PRODUCT_TYPE_MONTHLY_SUBSCRIPTION,
        PAYMENT_TYPE_BALANCE,
        PAYMENT_TYPE_DEPOSIT,
        PAYMENT_TYPE_FULL,
        MERCADO_PAGO_STATUS_APPROVED,
        MERCADO_PAGO_STATUS_IN_PROCESS,
        MERCADO_PAGO_STATUS_PENDING,
        PAYMENT_RETURN_STATUS_FAILURE,
        PAYMENT_RETURN_STATUS_PENDING,
        PAYMENT_RETURN_STATUS_SUCCESS,
    )
    from services import cancellation_service, class_service, credit_service, enrollment_service, notification_service, payment_service, waitlist_service
    from services.api_response import api_error, api_success
except ModuleNotFoundError:
    from .email_service import (
        send_admin_login_code,
        send_class_cancelled_email,
        send_credit_generated_email,
        send_waitlist_promotion_email,
    )
    from .mercadopago_config import get_mercadopago_client
    from .models import db, User
    # Importar todos los modelos requeridos
    from .models import Class, Enrollment, Attendance, Actividades, Credit, Credito, Notification, Payment, SystemSetting, WaitlistEntry
    from .constants import (
        DISCOUNT_PERCENTAGES,
        ENROLLMENT_STATUS_PENDING_PAYMENT,
        ENROLLMENT_TYPE_SINGLE,
        ENROLLMENT_TYPE_MONTHLY,
        WAITLIST_TYPE_INDIVIDUAL,
        WAITLIST_TYPE_MONTHLY,
        ENROLLMENT_PAYMENT_STATUS_EXPIRED,
        ENROLLMENT_PAYMENT_STATUS_PAID,
        ENROLLMENT_PAYMENT_STATUS_PENDING,
        PAYMENT_PRODUCT_TYPE_INDIVIDUAL_CLASS,
        PAYMENT_PRODUCT_TYPE_MONTHLY_SUBSCRIPTION,
        PAYMENT_TYPE_BALANCE,
        PAYMENT_TYPE_DEPOSIT,
        PAYMENT_TYPE_FULL,
        MERCADO_PAGO_STATUS_APPROVED,
        MERCADO_PAGO_STATUS_IN_PROCESS,
        MERCADO_PAGO_STATUS_PENDING,
        PAYMENT_RETURN_STATUS_FAILURE,
        PAYMENT_RETURN_STATUS_PENDING,
        PAYMENT_RETURN_STATUS_SUCCESS,
    )
    from .services import cancellation_service, class_service, credit_service, enrollment_service, notification_service, payment_service, waitlist_service
    from .services.api_response import api_error, api_success

# Carga variables de entorno desde .env
load_dotenv()

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ─── Configuración ────────────────────────────────────────────────────────────

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///app.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


def _is_production():
    return os.getenv("ENVIRONMENT", "").lower() == "production" or bool(os.getenv("PUBLIC_BACKEND_URL", "").strip())


app.config["SESSION_COOKIE_SAMESITE"] = os.getenv(
    "SESSION_COOKIE_SAMESITE",
    "None" if _is_production() else "Lax",
)
app.config["SESSION_COOKIE_SECURE"] = os.getenv(
    "SESSION_COOKIE_SECURE",
    "true" if _is_production() else "false",
).lower() == "true"

# Inicializa extensiones
db.init_app(app)


def _elapsed_ms(start_time):
    return round((time.perf_counter() - start_time) * 1000, 2)


@event.listens_for(Engine, "before_cursor_execute")
def _record_query_start(conn, cursor, statement, parameters, context, executemany):
    if has_request_context() and request.endpoint == "create_payment":
        context._payment_query_start = time.perf_counter()


@event.listens_for(Engine, "after_cursor_execute")
def _record_query_end(conn, cursor, statement, parameters, context, executemany):
    query_start = getattr(context, "_payment_query_start", None)
    if query_start is None or not has_request_context() or request.endpoint != "create_payment":
        return

    g.payment_query_count = getattr(g, "payment_query_count", 0) + 1
    g.payment_query_ms = getattr(g, "payment_query_ms", 0.0) + _elapsed_ms(query_start)

def _cors_origins():
    configured = os.getenv("FRONTEND_ORIGINS") or os.getenv("CORS_ORIGINS") or os.getenv("FRONTEND_URL", "")
    origins = [origin.strip().rstrip("/") for origin in configured.split(",") if origin.strip()]
    origins.extend([
        "http://localhost:5173",
        "http://localhost:5174",
    ])
    return list(dict.fromkeys(origins))


# CORS para frontend local y despliegues configurados
CORS(
    app,
    supports_credentials=True,
    origins=_cors_origins()
)

# ─── Migración de esquema mínimo para SQLite antiguo ─────────────────────────────────────────────

def upgrade_database_schema():
    inspector = inspect(db.engine)
    if "users" in inspector.get_table_names():
        columns = [column["name"] for column in inspector.get_columns("users")]
        if "apellido" not in columns:
            db.session.execute(text("ALTER TABLE users ADD COLUMN apellido VARCHAR(80)"))
        if "dni" not in columns:
            db.session.execute(text("ALTER TABLE users ADD COLUMN dni VARCHAR(20)"))
        if "telefono" not in columns:
            db.session.execute(text("ALTER TABLE users ADD COLUMN telefono VARCHAR(20)"))

    if "classes" in inspector.get_table_names():
        columns = [column["name"] for column in inspector.get_columns("classes")]
        if "fecha_hora" not in columns:
            db.session.execute(text("ALTER TABLE classes ADD COLUMN fecha_hora DATETIME"))
        if "cupoMaximo" not in columns:
            db.session.execute(text("ALTER TABLE classes ADD COLUMN cupoMaximo INTEGER DEFAULT 20"))
        if "id_actividad" not in columns:
            db.session.execute(text("ALTER TABLE classes ADD COLUMN id_actividad INTEGER"))
        if "estado" not in columns:
            db.session.execute(text(f"ALTER TABLE classes ADD COLUMN estado VARCHAR(20) DEFAULT '{Class.STATUS_ACTIVE}'"))
        if "duration_minutes" not in columns:
            db.session.execute(text("ALTER TABLE classes ADD COLUMN duration_minutes INTEGER DEFAULT 60"))
        if "descuento" not in columns:
            db.session.execute(text("ALTER TABLE classes ADD COLUMN descuento INTEGER DEFAULT 0"))
        if "room" not in columns:
            db.session.execute(text("ALTER TABLE classes ADD COLUMN room VARCHAR(50)"))
        db.session.commit()

    if "payments" in inspector.get_table_names():
        columns = [column["name"] for column in inspector.get_columns("payments")]
        if "class_id" not in columns:
            db.session.execute(text("ALTER TABLE payments ADD COLUMN class_id INTEGER"))
            db.session.commit()
        if "enrollment_id" not in columns:
            db.session.execute(text("ALTER TABLE payments ADD COLUMN enrollment_id INTEGER"))
            db.session.commit()
        if "product_type" not in columns:
            db.session.execute(text("ALTER TABLE payments ADD COLUMN product_type VARCHAR(30)"))
            db.session.commit()
        if "registered_by_user_id" not in columns:
            db.session.execute(text("ALTER TABLE payments ADD COLUMN registered_by_user_id INTEGER"))
            db.session.commit()
        if "notes" not in columns:
            db.session.execute(text("ALTER TABLE payments ADD COLUMN notes TEXT"))
            db.session.commit()

        db.session.execute(text(
            "UPDATE payments "
            "SET product_type = payment_type "
            "WHERE product_type IS NULL "
            "AND payment_type IN (:monthly_type, :individual_type, :legacy_single_type)"
        ), {
            "monthly_type": PAYMENT_PRODUCT_TYPE_MONTHLY_SUBSCRIPTION,
            "individual_type": PAYMENT_PRODUCT_TYPE_INDIVIDUAL_CLASS,
            "legacy_single_type": "single_class",
        })
        db.session.execute(text(
            "UPDATE payments "
            "SET product_type = :individual_type "
            "WHERE product_type = :legacy_single_type"
        ), {
            "individual_type": PAYMENT_PRODUCT_TYPE_INDIVIDUAL_CLASS,
            "legacy_single_type": "single_class",
        })
        db.session.execute(text(
            "UPDATE payments "
            "SET payment_type = :full_type "
            "WHERE payment_type IS NULL "
            "OR payment_type IN (:monthly_type, :individual_type, :legacy_single_type)"
        ), {
            "full_type": PAYMENT_TYPE_FULL,
            "monthly_type": PAYMENT_PRODUCT_TYPE_MONTHLY_SUBSCRIPTION,
            "individual_type": PAYMENT_PRODUCT_TYPE_INDIVIDUAL_CLASS,
            "legacy_single_type": "single_class",
        })
        db.session.commit()

    if "enrollments" in inspector.get_table_names():
        columns = [column["name"] for column in inspector.get_columns("enrollments")]
        if "tipo" not in columns:
            db.session.execute(text(f"ALTER TABLE enrollments ADD COLUMN tipo VARCHAR(20) DEFAULT '{ENROLLMENT_TYPE_SINGLE}'"))
        if "estado" not in columns:
            db.session.execute(text(f"ALTER TABLE enrollments ADD COLUMN estado VARCHAR(20) DEFAULT '{ENROLLMENT_STATUS_PENDING_PAYMENT}'"))
        if "requiere_reembolso" not in columns:
            db.session.execute(text("ALTER TABLE enrollments ADD COLUMN requiere_reembolso BOOLEAN DEFAULT 0"))
        if "created_at" not in columns:
            db.session.execute(text("ALTER TABLE enrollments ADD COLUMN created_at DATETIME"))
        if "total_amount" not in columns:
            db.session.execute(text("ALTER TABLE enrollments ADD COLUMN total_amount FLOAT DEFAULT 0"))
        if "paid_amount" not in columns:
            db.session.execute(text("ALTER TABLE enrollments ADD COLUMN paid_amount FLOAT DEFAULT 0"))
        if "remaining_amount" not in columns:
            db.session.execute(text("ALTER TABLE enrollments ADD COLUMN remaining_amount FLOAT DEFAULT 0"))
        if "payment_status" not in columns:
            db.session.execute(text(f"ALTER TABLE enrollments ADD COLUMN payment_status VARCHAR(20) DEFAULT '{ENROLLMENT_PAYMENT_STATUS_PENDING}'"))
        db.session.commit()

        db.session.execute(text("UPDATE enrollments SET estado = :new_status WHERE estado = :legacy_status"), {
            "new_status": Enrollment.STATUS_PAID,
            "legacy_status": Class.STATUS_ACTIVE,
        })
        db.session.execute(text("UPDATE enrollments SET estado = :new_status WHERE estado = :legacy_status"), {
            "new_status": Enrollment.STATUS_CANCELLED,
            "legacy_status": Class.STATUS_CANCELLED,
        })
        db.session.execute(text(
            "UPDATE enrollments SET payment_status = :expired_status WHERE estado = :expired_enrollment_status"
        ), {
            "expired_status": ENROLLMENT_PAYMENT_STATUS_EXPIRED,
            "expired_enrollment_status": Enrollment.STATUS_EXPIRED,
        })
        db.session.execute(text(
            "UPDATE enrollments SET payment_status = :paid_status WHERE estado = :paid_enrollment_status"
        ), {
            "paid_status": ENROLLMENT_PAYMENT_STATUS_PAID,
            "paid_enrollment_status": Enrollment.STATUS_PAID,
        })
        db.session.commit()

        for enrollment in Enrollment.query.all():
            payment_service.recompute_enrollment_payment_state(enrollment)
        db.session.commit()

    if "creditos" in inspector.get_table_names():
        columns = [column["name"] for column in inspector.get_columns("creditos")]
        if "origin_class_id" not in columns:
            db.session.execute(text("ALTER TABLE creditos ADD COLUMN origin_class_id INTEGER"))
        if "enrollment_id" not in columns:
            db.session.execute(text("ALTER TABLE creditos ADD COLUMN enrollment_id INTEGER"))
        if "used" not in columns:
            db.session.execute(text("ALTER TABLE creditos ADD COLUMN used BOOLEAN DEFAULT 0"))
        if "used_at" not in columns:
            db.session.execute(text("ALTER TABLE creditos ADD COLUMN used_at DATETIME"))
        if "created_at" not in columns:
            db.session.execute(text("ALTER TABLE creditos ADD COLUMN created_at DATETIME"))
        db.session.execute(text("UPDATE creditos SET used = 0 WHERE used IS NULL"))
        db.session.execute(text("UPDATE creditos SET used = 1 WHERE estado = :used_status"), {
            "used_status": Credit.STATUS_USED,
        })
        db.session.commit()

    if "notifications" in inspector.get_table_names():
        columns = [column["name"] for column in inspector.get_columns("notifications")]
        if "read" not in columns:
            db.session.execute(text("ALTER TABLE notifications ADD COLUMN read BOOLEAN DEFAULT 0"))
        if "created_at" not in columns:
            db.session.execute(text("ALTER TABLE notifications ADD COLUMN created_at DATETIME"))
        db.session.commit()

# ─── Crear tablas e insertar actividades base ───────────────────────────────────────────────────

def ensure_default_activities():
    default_names = ["Yoga", "Funcional", "Pilates"]
    existing_names = {act.name for act in Actividades.query.all()}

    for name in default_names:
        if name not in existing_names:
            db.session.add(Actividades(name=name))

    if db.session.new:
        db.session.commit()

with app.app_context():
    db.create_all()
    upgrade_database_schema()
    ensure_default_activities()

# ─── Helpers para el Catálogo ──────────────────────────────────────────────────

def _get_monthly_base_price(class_obj):
    y = class_obj.fecha_hora.year
    m = class_obj.fecha_hora.month
    wd = class_obj.fecha_hora.weekday()
    total_classes = 0
    for day in range(1, monthrange(y, m)[1] + 1):
        if datetime(y, m, day).weekday() == wd:
            total_classes += 1
    return 3000.0 * total_classes

def _enrollment_counts():
    base_counts = class_service.enrollment_counts()
    
    monthly_enrollments = Enrollment.query.filter(
        Enrollment.tipo == ENROLLMENT_TYPE_MONTHLY,
        Enrollment.estado.in_([Enrollment.STATUS_PENDING_PAYMENT, Enrollment.STATUS_PAID])
    ).all()
    
    if not monthly_enrollments:
        return base_counts
        
    # Filtramos las clases donde el usuario haya cancelado su asistencia mensual explícitamente
    user_ids = list(set(enr.user_id for enr in monthly_enrollments))
    cancelled_enrs = Enrollment.query.filter(
        Enrollment.user_id.in_(user_ids),
        Enrollment.estado.in_([Enrollment.STATUS_CANCELLED, "Cancelada", "cancelled"])
    ).all()
    cancelled_map = {(ce.user_id, ce.class_id) for ce in cancelled_enrs}

    # Obtenemos también las inscripciones activas para no sumar cupos por duplicado
    explicit_enrs = Enrollment.query.filter(
        Enrollment.user_id.in_(user_ids),
        Enrollment.estado.in_([Enrollment.STATUS_PENDING_PAYMENT, Enrollment.STATUS_PAID])
    ).all()
    explicit_map = {(ee.user_id, ee.class_id) for ee in explicit_enrs}

    for enr in monthly_enrollments:
        base_class = enr.class_
        if not base_class or not base_class.fecha_hora: continue
        
        y = base_class.fecha_hora.year
        m = base_class.fecha_hora.month
        end = datetime(y, m, monthrange(y, m)[1], 23, 59, 59)
        
        subsequent_classes = Class.query.filter(Class.id_actividad == base_class.id_actividad, Class.fecha_hora > base_class.fecha_hora, Class.fecha_hora <= end, Class.estado == Class.STATUS_ACTIVE).all()
        for c in subsequent_classes:
            if c.fecha_hora.weekday() == base_class.fecha_hora.weekday() and c.fecha_hora.strftime("%H:%M") == base_class.fecha_hora.strftime("%H:%M"):
                if (enr.user_id, c.id) not in cancelled_map and (enr.user_id, c.id) not in explicit_map:
                    base_counts[c.id] = base_counts.get(c.id, 0) + 1
    return base_counts


def _class_slot_payload(class_obj, enrolled_count):
    return class_service.class_slot_payload(class_obj, enrolled_count)


def _get_authenticated_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)


def _configured_amount(name, default):
    return payment_service.configured_amount(name, default)


def _app_timezone():
    timezone_name = os.getenv("APP_TIMEZONE", "America/Argentina/Buenos_Aires")
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        logger.warning("[Discount] timezone invalida=%s. Usando hora local del servidor.", timezone_name)
        return None


def _current_discount_datetime():
    timezone = _app_timezone()
    return datetime.now(timezone) if timezone else datetime.now()


def _valid_test_day(value):
    try:
        day = int(value)
    except (TypeError, ValueError):
        return None

    if 1 <= day <= 31:
        return day
    return None


def _discount_datetime_from_request():
    real_datetime = _current_discount_datetime()
    test_day = _valid_test_day(request.args.get("test_day"))
    test_mode = test_day is not None

    if test_mode:
        last_day = monthrange(real_datetime.year, real_datetime.month)[1]
        effective_datetime = real_datetime.replace(day=min(test_day, last_day))
    else:
        effective_datetime = real_datetime

    logger.info(
        "[Discount] test_mode=%s real_day=%s effective_day=%s",
        str(test_mode).lower(),
        real_datetime.day,
        effective_datetime.day,
    )

    return effective_datetime


def _datetime_in_app_timezone(value):
    if not value:
        return None

    timezone = _app_timezone()
    if not timezone:
        return value

    if value.tzinfo:
        return value.astimezone(timezone)
    return value.replace(tzinfo=timezone)


def _current_discount_period_percentage(current_datetime=None):
    return payment_service.current_discount_period_percentage(current_datetime)


def _payment_discount_percentage(current_datetime=None):
    return _current_discount_period_percentage(current_datetime)


def _discount_rules_payload(current_datetime=None):
    return payment_service.discount_rules_payload(current_datetime)


def _class_has_finished(class_obj, current_datetime=None):
    return payment_service.class_has_finished(class_obj, current_datetime)


def _payment_expires_at(class_obj):
    return payment_service.payment_expires_at(class_obj)


def _payment_amount(payment_type, payment_option):
    return payment_service.payment_amount(payment_type, payment_option)


def _calculate_final_amount(amount, discount_percentage):
    return payment_service.calculate_final_amount(amount, discount_percentage)


def _payment_quote(payment_type, payment_option, current_datetime=None):
    quote = payment_service.payment_quote(payment_type, payment_option, current_datetime)
    if payment_type == "single_class":
        quote["discount_percentage"] = 0
        quote["final_amount"] = quote.get("amount", 0)
    return quote


def _payment_type_for_enrollment(enrollment):
    return payment_service.payment_type_for_enrollment(enrollment)


def _expire_enrollment_if_needed(enrollment, current_datetime=None):
    return enrollment_service.expire_enrollment_if_needed(enrollment, current_datetime)


def _has_approved_payment(enrollment):
    return payment_service.has_approved_payment(enrollment)


def _credit_expiration_from(current_datetime=None):
    return credit_service.credit_expiration_from(current_datetime)


def _is_credit_valid(credit, activity_id, current_datetime=None):
    return credit_service.is_credit_valid(credit, activity_id, current_datetime)


def _available_credit_for_user_activity(user_id, activity_id, current_datetime=None):
    return credit_service.available_credit_for_user_activity(user_id, activity_id, current_datetime)


def _consume_credit_for_enrollment(credit, enrollment, current_datetime=None):
    return credit_service.consume_credit_for_enrollment(credit, enrollment, current_datetime)


def _create_cancellation_notification(enrollment, class_obj, credited):
    return notification_service.create_cancellation_notification(enrollment, class_obj, credited)


def _credit_exists_for_cancelled_enrollment(enrollment, class_obj):
    return credit_service.credit_exists_for_cancelled_enrollment(enrollment, class_obj)


def _generate_credit_for_paid_enrollment(enrollment, class_obj, current_datetime=None):
    return credit_service.generate_credit_for_paid_enrollment(enrollment, class_obj, current_datetime)


def _expire_payment_for_enrollment(enrollment, current_datetime=None):
    return payment_service.expire_payment_for_enrollment(enrollment, current_datetime)


def _restore_future_expired_enrollment_if_needed(enrollment, current_datetime=None):
    return enrollment_service.restore_future_expired_enrollment_if_needed(enrollment, current_datetime)


def _class_capacity(class_obj):
    return enrollment_service.class_capacity(class_obj)


def _validate_class_available_for_enrollment(class_obj, current_datetime):
    return enrollment_service.validate_class_available_for_enrollment(class_obj, current_datetime)


def _validate_enrollment_payable(enrollment, current_user, current_datetime):
    error, status_code = enrollment_service.validate_enrollment_payable(enrollment, current_user, current_datetime)
    if error and enrollment:
        db.session.commit()
    return error, status_code


def _enrollment_has_other_approved_payment(payment):
    return payment_service.enrollment_has_other_approved_payment(payment)


def _payment_would_overpay(payment):
    return payment_service.payment_would_overpay(payment)


def _enrollment_payment_quote(enrollment, current_datetime=None):
    quote = payment_service.enrollment_payment_quote(enrollment, current_datetime)
    discount = int(quote.get("discount_percentage", 0))
    
    if enrollment.tipo == ENROLLMENT_TYPE_SINGLE:
        amount = float(quote.get("amount", 0))
    else:
        amount = _get_monthly_base_price(enrollment.class_)
        
    quote["amount"] = amount
    quote["discount_percentage"] = discount
    quote["final_amount"] = _calculate_final_amount(amount, discount)
    return quote


def _enrollment_payload(enrollment, current_datetime=None):
    payload = enrollment_service.enrollment_payload(enrollment, current_datetime)
    quote = payment_service.enrollment_payment_quote(enrollment, current_datetime)
    discount = int(quote.get("discount_percentage", 0))
    
    if enrollment.tipo == ENROLLMENT_TYPE_SINGLE:
        amount = 3000.0
    else:
        amount = _get_monthly_base_price(enrollment.class_)
        
    payload["amount"] = amount
    payload["discount_percentage"] = discount
    payload["final_amount"] = _calculate_final_amount(amount, discount)
    if not float(payload.get("paid_amount") or 0):
        enrollment.total_amount = round(payload["final_amount"], 2)
        enrollment.paid_amount = 0
        enrollment.remaining_amount = enrollment.total_amount
        payload["total_amount"] = enrollment.total_amount
        payload["paid_amount"] = enrollment.paid_amount
        payload["remaining_amount"] = enrollment.remaining_amount
    elif not float(payload.get("total_amount") or 0):
        payload["total_amount"] = payload["final_amount"]
    deposit_amount, deposit_final_amount = payment_service.payment_amounts_for_type(
        enrollment,
        PAYMENT_TYPE_DEPOSIT,
        amount,
        payload["final_amount"],
    )
    payload["full_payment_amount"] = payload["remaining_amount"] or payload["final_amount"]
    payload["deposit_amount"] = deposit_final_amount
    payload["deposit_percentage"] = payment_service.deposit_percentage()
    payload["balance_amount"] = max((payload.get("total_amount") or 0) - (payload.get("paid_amount") or 0), 0)
    payload["cancellation_will_generate_credit"] = _has_approved_payment(enrollment)
    payload["is_cancelable"] = False  # Oculta el botón en la lista de pagos pendientes
    return payload


def _payment_payload(payment, current_datetime=None):
    payload = payment.to_dict()
    enrollment = payment.enrollment
    if enrollment:
        payload["enrollment_estado"] = enrollment.estado
        payload["enrollment_payment_status"] = enrollment.payment_status
        payload["enrollment_is_cancelable"] = False  # Oculta el botón en detalles de pago
        deadline = enrollment_service.cancellation_deadline_for_class(enrollment.class_)
        payload["enrollment_cancellation_deadline"] = deadline.isoformat() if deadline else None
        payload["enrollment_cancellation_will_generate_credit"] = _has_approved_payment(enrollment)
    return payload


def _credit_enrollment_response(enrollment, credit, current_datetime=None, status_code=201):
    return api_success(
        enrollment_service.credit_enrollment_payload(enrollment, credit, current_datetime),
        message="Inscripción realizada utilizando crédito",
        status_code=status_code,
    )


def _log_discount_quote(current_datetime, class_obj, discount_percentage, amount, final_amount):
    return payment_service.log_discount_quote(current_datetime, class_obj, discount_percentage, amount, final_amount)


def _payment_error_message(status_detail):
    return payment_service.payment_error_message(status_detail)


def _frontend_payments_url(status, message=None):
    return payment_service.frontend_payments_url(status, message)


def _configured_url(name, default):
    return payment_service.configured_url(name, default)


def _public_backend_url():
    configured = _configured_url("PUBLIC_BACKEND_URL", "")
    if configured:
        return configured.rstrip("/")
    legacy_configured = _configured_url("BACKEND_PUBLIC_URL", "")
    if legacy_configured:
        return legacy_configured.rstrip("/")
    return ""


def _mercado_pago_callback_url(name, path, default):
    configured = _configured_url(name, "")
    if configured:
        return configured
    public_backend_url = _public_backend_url()
    if public_backend_url:
        return f"{public_backend_url}{path}"
    return default


def _is_absolute_http_url(value):
    return payment_service.is_absolute_http_url(value)


def _validate_mercado_pago_back_urls(preference_data):
    return payment_service.validate_mercado_pago_back_urls(preference_data)


def _log_mercado_pago_payload(preference_data):
    return payment_service.log_mercado_pago_payload(preference_data)


def _log_mercado_pago_response(preference_result):
    return payment_service.log_mercado_pago_response(preference_result)


def _mercado_pago_checkout_url(preference_response):
    return payment_service.mercado_pago_checkout_url(preference_response)


def _mercado_pago_payer_email(default_email):
    return payment_service.mercado_pago_payer_email(default_email)


def _mercado_pago_payer_payload(user):
    payer = {"name": user.username}
    payer_email = _mercado_pago_payer_email(user.email)
    if payer_email:
        payer["email"] = payer_email
    return payer


def _mercado_pago_notification_url():
    configured = os.getenv("MERCADOPAGO_NOTIFICATION_URL", "").strip()
    if configured:
        return configured

    public_backend_url = _public_backend_url()
    if public_backend_url:
        return f"{public_backend_url}/api/payments/webhook"

    success_url = os.getenv("PAYMENT_SUCCESS_URL", "").strip()
    marker = "/api/payments/return/success"
    if marker in success_url:
        return f"{success_url.split(marker, 1)[0]}/api/payments/webhook"

    return "http://localhost:5000/api/payments/webhook"


def _mercado_pago_payment_response(mercado_pago_payment_id):
    if not mercado_pago_payment_id:
        return None
    try:
        result = get_mercadopago_client().payment().get(mercado_pago_payment_id)
    except Exception:
        logger.exception("[MercadoPago] no_se_pudo_consultar_pago mp_payment_id=%s", mercado_pago_payment_id)
        return None

    if not isinstance(result, dict):
        logger.error("[MercadoPago] consulta_pago_respuesta_invalida response=%s", result)
        return None
    if result.get("status") not in [200, 201]:
        logger.error("[MercadoPago] consulta_pago_rechazada response=%s", result)
        return None

    response = result.get("response")
    return response if isinstance(response, dict) else None


def _payment_from_mercado_pago_response(mp_payment):
    if not isinstance(mp_payment, dict):
        return None

    external_reference = mp_payment.get("external_reference")
    if external_reference:
        payment = Payment.query.get(external_reference)
        if payment:
            return payment

    preference_id = mp_payment.get("preference_id")
    if preference_id:
        return Payment.query.filter_by(mercado_pago_preference_id=preference_id).first()

    return None


def _apply_mercado_pago_status(payment, mercado_pago_status, status_detail=None, mercado_pago_payment_id=None, current_datetime=None):
    current_datetime = current_datetime or _current_discount_datetime()
    if mercado_pago_payment_id:
        payment.mercado_pago_payment_id = str(mercado_pago_payment_id)

    if payment.enrollment and payment.enrollment.estado == Enrollment.STATUS_CANCELLED and payment.status != Payment.STATUS_APPROVED:
        payment.status = Payment.STATUS_EXPIRED
        payment_service.recompute_enrollment_payment_state(payment.enrollment, current_datetime)
        logger.info(
            "[MercadoPago] callback_ignorado_inscripcion_cancelada payment_id=%s enrollment_id=%s",
            payment.id,
            payment.enrollment_id,
        )
        return PAYMENT_RETURN_STATUS_FAILURE, "La inscripción fue cancelada"

    if payment.status == Payment.STATUS_APPROVED:
        payment_service.expire_equivalent_pending_payments(payment)
        if payment.enrollment:
            payment_service.recompute_enrollment_payment_state(payment.enrollment, current_datetime)
        return PAYMENT_RETURN_STATUS_SUCCESS, None

    if payment.enrollment and _class_has_finished(payment.enrollment.class_, current_datetime):
        payment.status = Payment.STATUS_EXPIRED
        if payment.enrollment.estado == Enrollment.STATUS_PENDING_PAYMENT:
            payment.enrollment.estado = Enrollment.STATUS_EXPIRED
        payment_service.recompute_enrollment_payment_state(payment.enrollment, current_datetime)
        return PAYMENT_RETURN_STATUS_FAILURE, "El período de pago de la inscripción venció"

    if mercado_pago_status == MERCADO_PAGO_STATUS_APPROVED:
        if _payment_would_overpay(payment):
            payment.status = Payment.STATUS_REJECTED
            return PAYMENT_RETURN_STATUS_FAILURE, "El pago supera el saldo pendiente"

        payment.status = Payment.STATUS_APPROVED
        payment_service.expire_equivalent_pending_payments(payment)
        if payment.enrollment:
            payment_service.recompute_enrollment_payment_state(payment.enrollment, current_datetime)
        return PAYMENT_RETURN_STATUS_SUCCESS, None

    if mercado_pago_status in [MERCADO_PAGO_STATUS_PENDING, MERCADO_PAGO_STATUS_IN_PROCESS]:
        payment.status = Payment.STATUS_PENDING
        return PAYMENT_RETURN_STATUS_PENDING, None

    payment.status = Payment.STATUS_REJECTED
    return PAYMENT_RETURN_STATUS_FAILURE, _payment_error_message(status_detail)


# Helper para promover lista de espera que usaremos en todas las cancelaciones
def _promote_waitlist_for_class(class_obj):
    try:
        # Buscar y ordenar primero la lista mensual
        waitlist_entries_monthly = WaitlistEntry.query.filter_by(
            class_id=class_obj.id,
            type=WAITLIST_TYPE_MONTHLY
        ).order_by(WaitlistEntry.created_at.asc()).all()
        
        # Buscar y ordenar luego la lista individual
        waitlist_entries_individual = WaitlistEntry.query.filter_by(
            class_id=class_obj.id,
            type=WAITLIST_TYPE_INDIVIDUAL
        ).order_by(WaitlistEntry.created_at.asc()).all()
        
        # Unir dando prioridad a los mensuales
        waitlist_entries = waitlist_entries_monthly + waitlist_entries_individual

        promoted = False
        for next_in_waitlist in waitlist_entries:
            user_to_promote = next_in_waitlist.user

            existing_enr = Enrollment.query.filter_by(
                user_id=user_to_promote.id,
                class_id=class_obj.id
            ).first()

            if existing_enr and existing_enr.estado in [Enrollment.STATUS_PENDING_PAYMENT, Enrollment.STATUS_PAID]:
                db.session.delete(next_in_waitlist)
                continue
            
            new_tipo = ENROLLMENT_TYPE_MONTHLY if next_in_waitlist.type == WAITLIST_TYPE_MONTHLY else ENROLLMENT_TYPE_SINGLE

            if existing_enr:
                existing_enr.estado = Enrollment.STATUS_PENDING_PAYMENT
                existing_enr.tipo = new_tipo
                existing_enr.requiere_reembolso = False
                existing_enr.total_amount = 0
                existing_enr.paid_amount = 0
                existing_enr.remaining_amount = 0
                existing_enr.payment_status = Enrollment.PAYMENT_STATUS_PENDING
                new_enrollment = existing_enr
            else:
                new_enrollment = Enrollment(
                    user_id=user_to_promote.id,
                    class_id=class_obj.id,
                    tipo=new_tipo,
                    estado=Enrollment.STATUS_PENDING_PAYMENT,
                )
                db.session.add(new_enrollment)
            
            db.session.delete(next_in_waitlist)
            notification_service.create_waitlist_promotion_notification(user_to_promote, class_obj)
            db.session.commit()

            other_pending_enrollments = Enrollment.query.filter(
                Enrollment.user_id == new_enrollment.user_id,
                Enrollment.id != new_enrollment.id,
                Enrollment.estado == Enrollment.STATUS_PENDING_PAYMENT,
            ).all()
            send_waitlist_promotion_email(user_to_promote, class_obj, new_enrollment, other_pending_enrollments)
            promoted = True
            break
            
        if not promoted and waitlist_entries:
            db.session.commit()
    except Exception as err:
        db.session.rollback()
        logger.exception("[Cancelaciones] Error al promover desde lista de espera: %s", err)

def _shift_monthly_parent_if_needed(enrollment):
    """
    Si este enrollment es el parent de una suscripción mensual activa, 
    lo mueve a la próxima clase del mes para no perder el resto de las clases implícitas,
    y devuelve un enrollment 'dummy' para cancelar la clase actual.
    """
    if enrollment.tipo != ENROLLMENT_TYPE_MONTHLY or enrollment.estado not in [Enrollment.STATUS_PENDING_PAYMENT, Enrollment.STATUS_PAID]:
        return enrollment

    class_obj = enrollment.class_
    if not class_obj or not class_obj.fecha_hora:
        return enrollment

    month_end = datetime(class_obj.fecha_hora.year, class_obj.fecha_hora.month, monthrange(class_obj.fecha_hora.year, class_obj.fecha_hora.month)[1], 23, 59, 59)
    next_classes = Class.query.filter(
        Class.id_actividad == class_obj.id_actividad,
        Class.fecha_hora > class_obj.fecha_hora,
        Class.fecha_hora <= month_end,
        Class.estado == Class.STATUS_ACTIVE
    ).order_by(Class.fecha_hora.asc()).all()
    
    valid_next_class = None
    for nc in next_classes:
        if nc.fecha_hora.weekday() == class_obj.fecha_hora.weekday() and nc.fecha_hora.strftime("%H:%M") == class_obj.fecha_hora.strftime("%H:%M"):
            valid_next_class = nc
            break
            
    if valid_next_class:
        # Movemos el parent enrollment a la próxima clase
        enrollment.class_id = valid_next_class.id
        # Creamos un enrollment "dummy" para la clase actual que será cancelado
        dummy_enr = Enrollment(
            user_id=enrollment.user_id,
            class_id=class_obj.id,
            tipo=ENROLLMENT_TYPE_MONTHLY,
            estado=enrollment.estado,
            payment_status=enrollment.payment_status,
            total_amount=0, paid_amount=0, remaining_amount=0, requiere_reembolso=False
        )
        db.session.add(dummy_enr)
        db.session.flush()
        return dummy_enr
        
    return enrollment

def _materialize_implicit_enrollments_for_cancellation(class_obj):
    if not class_obj.fecha_hora:
        return
        
    month_start = datetime(class_obj.fecha_hora.year, class_obj.fecha_hora.month, 1)
    last_day = monthrange(class_obj.fecha_hora.year, class_obj.fecha_hora.month)[1]
    month_end = datetime(class_obj.fecha_hora.year, class_obj.fecha_hora.month, last_day, 23, 59, 59)

    monthly_enrs = Enrollment.query.join(Class).filter(
        Enrollment.tipo == ENROLLMENT_TYPE_MONTHLY,
        Enrollment.estado.in_([Enrollment.STATUS_PENDING_PAYMENT, Enrollment.STATUS_PAID]),
        Class.id_actividad == class_obj.id_actividad,
        Class.fecha_hora >= month_start,
        Class.fecha_hora <= month_end
    ).all()

    for enr in monthly_enrs:
        if enr.class_.fecha_hora.weekday() == class_obj.fecha_hora.weekday() and enr.class_.fecha_hora.strftime("%H:%M") == class_obj.fecha_hora.strftime("%H:%M"):
            if enr.class_id == class_obj.id:
                # Es el parent
                _shift_monthly_parent_if_needed(enr)
            elif class_obj.fecha_hora > enr.class_.fecha_hora:
                # Es implícita
                existing = Enrollment.query.filter_by(user_id=enr.user_id, class_id=class_obj.id).first()
                if not existing:
                    dummy_enr = Enrollment(
                        user_id=enr.user_id,
                        class_id=class_obj.id,
                        tipo=ENROLLMENT_TYPE_MONTHLY,
                        estado=enr.estado,
                        payment_status=enr.payment_status,
                        total_amount=0, paid_amount=0, remaining_amount=0, requiere_reembolso=False
                    )
                    db.session.add(dummy_enr)
    db.session.flush()

# ─── Rutas API: Autenticación ─────────────────────────────────────────────────

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    apellido = data.get("apellido")
    email = data.get("email")
    dni = data.get("dni")
    telefono = data.get("telefono")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({"error": "Todos los campos son obligatorios"}), 400

    if len(password) < 6:
        return jsonify({"error": "La contraseña debe tener al menos 6 caracteres"}), 400

    if not re.search(r'[A-Z]', password):
        return jsonify({"error": "La contraseña debe incluir al menos una letra mayúscula"}), 400

    if not re.search(r'[^a-zA-Z0-9]', password):
        return jsonify({"error": "La contraseña debe incluir al menos un símbolo especial (?, !, \", #, etc.)"}), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "El email ya está registrado"}), 400

    new_user = User(username=username, apellido=apellido, email=email, dni=dni, telefono=telefono)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "Usuario registrado correctamente"}), 201


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 401

    if not user.check_password(password):
        return jsonify({"error": "Contraseña incorrecta"}), 401

    session["user_id"] = user.id
    return jsonify({
        "message": "Login exitoso",
        "user": {"id": user.id, "username": user.username, "email": user.email, "role": user.role}
    }), 200


@app.route("/api/admin-login/request", methods=["POST"])
def admin_login_request():
    data = request.get_json()
    email = data.get("email", "").strip()
    password = data.get("password", "")
    if not email or not password:
        return jsonify({"error": "Debe ingresar email y contraseña"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 401
        
    if not user.check_password(password):
        return jsonify({"error": "Contraseña incorrecta"}), 401
        
    if user.role != "admin":
        return jsonify({"error": "El usuario no es administrador"}), 403

    code = f"{random.randint(0, 999999):06d}"
    session["admin_login_email"] = email
    session["admin_login_code"] = code
    session["admin_login_code_expires_at"] = (datetime.utcnow() + timedelta(minutes=5)).timestamp()

    if not send_admin_login_code(user, code):
        session.pop("admin_login_email", None)
        session.pop("admin_login_code", None)
        session.pop("admin_login_code_expires_at", None)
        return jsonify({"error": "No se pudo enviar el código de verificación por email"}), 500

    return jsonify({"message": "Se envió un código de verificación al email"}), 200


@app.route("/api/admin-login/verify", methods=["POST"])
def admin_login_verify():
    data = request.get_json()
    email = data.get("email", "").strip()
    code = data.get("code", "").strip()

    if not email or not code:
        return jsonify({"error": "Email y código son obligatorios"}), 400

    pending_email = session.get("admin_login_email")
    pending_code = session.get("admin_login_code")
    expires_at = session.get("admin_login_code_expires_at")

    if not pending_email or not pending_code or not expires_at:
        return jsonify({"error": "No hay un código pendiente. Solicitá uno primero."}), 400

    if email != pending_email or code != pending_code:
        return jsonify({"error": "Código incorrecto"}), 401

    if datetime.utcnow().timestamp() > expires_at:
        session.pop("admin_login_email", None)
        session.pop("admin_login_code", None)
        session.pop("admin_login_code_expires_at", None)
        return jsonify({"error": "El código expiró. Solicitá uno nuevo."}), 401

    user = User.query.filter_by(email=email, role="admin").first()
    if not user:
        return jsonify({"error": "Administrador no encontrado"}), 401

    session["user_id"] = user.id
    session.pop("admin_login_email", None)
    session.pop("admin_login_code", None)
    session.pop("admin_login_code_expires_at", None)

    return jsonify({
        "message": "Login exitoso",
        "user": {"id": user.id, "username": user.username, "email": user.email, "role": user.role}
    }), 200


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Sesión cerrada"}), 200


@app.route("/api/me", methods=["GET"])
def me():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "No autenticado"}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    return jsonify({
        "user": {
            "id": user.id, 
            "username": user.username, 
            "apellido": user.apellido,
            "email": user.email, 
            "dni": user.dni,
            "telefono": user.telefono,
            "role": user.role
        }
    }), 200

@app.route("/api/me", methods=["PUT"])
def update_profile():
    """Actualiza el perfil del usuario actual."""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "No autenticado"}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    data = request.get_json()
    
    # Validar que los campos obligatorios no estén vacíos
    username = data.get("username", "").strip()
    apellido = data.get("apellido", "").strip()
    telefono = data.get("telefono", "").strip()
    dni = data.get("dni", "").strip()
    
    if not all([username, apellido, telefono, dni]):
        return jsonify({"error": "Todos los campos son obligatorios"}), 400
    
    # Actualizar los datos del usuario
    user.username = username
    user.apellido = apellido
    user.telefono = telefono
    user.dni = dni
    
    try:
        db.session.commit()
        return jsonify({
            "message": "Perfil actualizado correctamente",
            "user": user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al actualizar perfil: {e}")
        return jsonify({"error": "Error al actualizar el perfil"}), 500

@app.route("/api/me/change-password", methods=["POST"])
def change_password():
    """Cambia la contraseña del usuario actual."""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "No autenticado"}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    data = request.get_json()
    current_password = data.get("current_password")
    new_password = data.get("new_password")
    confirm_password = data.get("confirm_password")

    if not all([current_password, new_password, confirm_password]):
        return jsonify({"error": "Todos los campos son obligatorios"}), 400

    if not user.check_password(current_password):
        return jsonify({"error": "La contraseña actual es incorrecta"}), 400

    if user.check_password(new_password):
        return jsonify({"error": "La nueva contraseña no puede ser igual a la actual"}), 400

    if new_password != confirm_password:
        return jsonify({"error": "Las nuevas contraseñas no coinciden"}), 400

    if len(new_password) < 6:
        return jsonify({"error": "La nueva contraseña debe tener al menos 6 caracteres"}), 400

    user.set_password(new_password)

    try:
        db.session.commit()
        return jsonify({"message": "Contraseña actualizada correctamente"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al cambiar la contraseña: {e}")
        return jsonify({"error": "Error al cambiar la contraseña"}), 500


@app.route("/api/me", methods=["DELETE"])
def delete_my_account():
    """Elimina la cuenta del usuario actual."""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "No autenticado"}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    data = request.get_json() or {}
    password = data.get("password")

    if not password:
        return jsonify({"error": "La contraseña es requerida para eliminar la cuenta"}), 400

    if not user.check_password(password):
        return jsonify({"error": "Contraseña incorrecta"}), 403

    # Validación explícita: Bloqueamos la eliminación solo si hay inscripciones activas
    # o pagos aprobados, para evitar borrar historial contable o de clases en cascada.
    # Las inscripciones canceladas o vencidas (sin pagos) permiten borrar la cuenta.
    active_enrollments = [e for e in user.enrollments if e.estado not in [Enrollment.STATUS_CANCELLED, Enrollment.STATUS_EXPIRED]]
    approved_payments = [p for p in user.payments if p.status == Payment.STATUS_APPROVED]

    if active_enrollments or approved_payments:
        return jsonify({"error": "No se puede eliminar la cuenta porque tienes inscripciones activas"}), 400

    try:
        db.session.delete(user)
        db.session.commit()
        # Cerramos la sesión
        session.clear()
        return jsonify({"message": "Cuenta eliminada correctamente"}), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "No se puede eliminar la cuenta porque tiene registros asociados (pagos, inscripciones, etc)."}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al eliminar cuenta: {e}")
        return jsonify({"error": "Error al eliminar la cuenta"}), 500

# ─── Rutas API: Actividades, Usuarios y Catálogo ────────────────────────────────────────

@app.route("/api/actividades", methods=["GET"])
def get_actividades():
    actividades = Actividades.query.all()
    return jsonify([{"id": ac.id, "name": ac.name} for ac in actividades]), 200


@app.route("/api/users", methods=["GET"])
def get_users():
    current_user = _get_authenticated_user()
    if not current_user:
        return jsonify({"error": "No autenticado"}), 401

    if current_user.role not in ["admin", "employee"]:
        return jsonify({"error": "No tienes permisos para listar usuarios"}), 403

    users = User.query.order_by(
        case(
            (User.role == "admin", 1),
            (User.role == "employee", 2),
            (User.role == "client", 3),
            else_=4
        ),
        User.apellido,
        User.username
    ).all()
    return jsonify([
        {
            "id": u.id,
            "username": u.username,
            "apellido": u.apellido,
            "email": u.email,
            "dni": u.dni,
            "telefono": u.telefono,
            "role": u.role
        } for u in users
    ]), 200


@app.route("/api/admin/reportes/usuarios/<int:user_id>/detalles", methods=["GET"])
def get_user_details(user_id):
    current_user = _get_authenticated_user()
    if not current_user or current_user.role not in ["admin", "employee"]:
        return jsonify({"error": "No tienes permisos"}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    enrollments_data = []
    
    explicit_enrollments = Enrollment.query.filter_by(user_id=user.id).all()
    explicit_map = {enr.class_id: enr for enr in explicit_enrollments}
    
    # Filtramos las inscripciones mensuales
    monthly_enrollments = [enr for enr in explicit_enrollments if enr.tipo == ENROLLMENT_TYPE_MONTHLY and enr.estado in [Enrollment.STATUS_PENDING_PAYMENT, Enrollment.STATUS_PAID]]

    for enr in explicit_enrollments:
        class_obj = enr.class_
        if not class_obj: continue
        
        enrollments_data.append({
            "id": enr.id,
            "actividad": class_obj.actividad.name if class_obj.actividad else class_obj.name,
            "fecha_hora": class_obj.fecha_hora.isoformat() if class_obj.fecha_hora else None,
            "tipo": enr.tipo,
            "estado_inscripcion": enr.estado,
            "estado_clase": class_obj.estado,
            "requiere_reembolso": enr.requiere_reembolso,
            "estado_pago": enr.payment_status,
            "monto_total": enr.total_amount,
            "saldo": enr.remaining_amount
        })

    # Agregamos las clases implícitas del mes
    for enr in monthly_enrollments:
        class_obj = enr.class_
        if not class_obj or not class_obj.fecha_hora: continue
        
        last_day = monthrange(class_obj.fecha_hora.year, class_obj.fecha_hora.month)[1]
        month_end = datetime(class_obj.fecha_hora.year, class_obj.fecha_hora.month, last_day, 23, 59, 59)
        
        implicit_classes = Class.query.filter(
            Class.id_actividad == class_obj.id_actividad,
            Class.fecha_hora > class_obj.fecha_hora,
            Class.fecha_hora <= month_end
        ).all()

        for ic in implicit_classes:
            if ic.fecha_hora.weekday() == class_obj.fecha_hora.weekday() and ic.fecha_hora.strftime("%H:%M") == class_obj.fecha_hora.strftime("%H:%M"):
                if ic.id in explicit_map:
                    continue
                
                enrollments_data.append({
                    "id": f"implicit_{ic.id}_{enr.id}",
                    "actividad": ic.actividad.name if ic.actividad else ic.name,
                    "fecha_hora": ic.fecha_hora.isoformat(),
                    "tipo": "Mensual",
                    "estado_inscripcion": enr.estado,
                    "estado_clase": ic.estado,
                    "requiere_reembolso": False,
                    "estado_pago": enr.payment_status,
                    "monto_total": 0,
                    "saldo": 0
                })

    enrollments_data.sort(key=lambda x: x["fecha_hora"] if x["fecha_hora"] else "", reverse=True)

    return jsonify({
        "user": user.to_dict(),
        "enrollments": enrollments_data
    }), 200


@app.route("/api/users", methods=["POST"])
def create_user():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "No autenticado"}), 401

    current_user = User.query.get(user_id)
    if not current_user or current_user.role not in ["admin", "employee"]:
        return jsonify({"error": "No tienes permisos para crear usuarios"}), 403

    data = request.get_json()
    username = data.get("username", "").strip()
    apellido = data.get("apellido", "").strip()
    email = data.get("email", "").strip()
    dni = data.get("dni", "").strip()
    telefono = data.get("telefono", "").strip()
    password = data.get("password", "").strip()
    role = data.get("role", "client").strip()

    if not all([username, apellido, email, dni, telefono, password]):
        return jsonify({"error": "Todos los campos son obligatorios"}), 400

    if len(password) < 6:
        return jsonify({"error": "La contraseña debe tener al menos 6 caracteres"}), 400

    if not re.search(r'[A-Z]', password):
        return jsonify({"error": "La contraseña debe incluir al menos una letra mayúscula"}), 400

    if not re.search(r'[^a-zA-Z0-9]', password):
        return jsonify({"error": "La contraseña debe incluir al menos un símbolo especial (?, !, \", #, etc.)"}), 400

    existing_email = User.query.filter_by(email=email).first()
    if existing_email:
        return jsonify({"error": "El email ya está registrado"}), 400

    # Validación de seguridad:
    if current_user.role == "employee" and role != "client":
        return jsonify({"error": "Los empleados solo pueden crear usuarios cliente"}), 403
        
    if current_user.role == "admin" and role not in ["client", "employee", "admin"]:
        role = "client"

    new_user = User(username=username, apellido=apellido, email=email, dni=dni, telefono=telefono, role=role)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "Usuario creado exitosamente", "user": new_user.to_dict()}), 201


@app.route("/api/actividades/<int:actividad_id>/classes", methods=["GET"])
def get_activity_classes(actividad_id):
    # 🌟 FILTRADO SEGURO: Enviamos al frontend TODAS las clases activas para poder validar conflictos de salón
    classes = Class.query.filter_by(estado=Class.STATUS_ACTIVE).all()
    rooms = dict(db.session.execute(text("SELECT id, room FROM classes")).fetchall())
    return jsonify({
        "classes": [{"id": c.id, "fecha_hora": c.fecha_hora.isoformat(), "time": c.fecha_hora.strftime("%H:%M"), "activity_id": c.id_actividad, "room": rooms.get(c.id)} for c in classes]
    }), 200


@app.route("/api/catalog", methods=["GET"])
def get_catalog():
    enrollment_map = _enrollment_counts()
    capacity_classes = []
    for class_obj in Class.query.filter_by(estado=Class.STATUS_ACTIVE).all():
        enrolled_count = enrollment_map.get(class_obj.id, 0)
        cupo_max = class_obj.cupoMaximo if class_obj.cupoMaximo is not None else 20
        if enrolled_count < cupo_max:
            capacity_classes.append(_class_slot_payload(class_obj, enrolled_count))
    return jsonify({"classes": capacity_classes}), 200


@app.route("/api/classes/all", methods=["GET"])
def get_all_classes():
    """Devuelve TODAS las clases con conteo de inscritos.
    Utilizado principalmente por el Dashboard del staff."""
    enrollment_map = _enrollment_counts()
    class_payloads = []
    for class_obj in Class.query.all():
        enrolled_count = enrollment_map.get(class_obj.id, 0)
        payload = _class_slot_payload(class_obj, enrolled_count)
        class_payloads.append(payload)
    return jsonify({"classes": class_payloads}), 200


@app.route("/api/catalog/availability", methods=["GET"])
def get_catalog_availability():
    actividad_id = request.args.get("actividad_id", type=int)
    fecha = request.args.get("fecha")

    if not actividad_id or not fecha:
        return jsonify({"error": "actividad_id y fecha son requeridos"}), 400

    try:
        day = datetime.strptime(fecha, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "fecha inválida (use YYYY-MM-DD)"}), 400

    actividad = Actividades.query.get(actividad_id)
    if not actividad:
        return jsonify({"error": "Actividad no encontrada"}), 404

    enrollment_map = _enrollment_counts()
    slots = []
    full_count = 0

    # 🌟 Traemos solo las clases activas para que no bloqueen horarios en el catálogo
    classes = Class.query.filter_by(id_actividad=actividad_id, estado=Class.STATUS_ACTIVE).filter(db.func.date(Class.fecha_hora) == day).order_by(Class.fecha_hora).all()

    now = datetime.now()

    for class_obj in classes:
        if class_obj.fecha_hora and class_obj.fecha_hora <= now:
            continue
            
        enrolled_count = enrollment_map.get(class_obj.id, 0)
        slot = _class_slot_payload(class_obj, enrolled_count)
        if slot["available_spots"] <= 0:
            full_count += 1
        slots.append(slot)

    return jsonify({
        "actividad": actividad.name,
        "fecha": fecha,
        "slots": slots,
        "available": slots,
        "full_count": full_count,
    }), 200


@app.route("/api/catalog/days", methods=["GET"])
def get_catalog_days():
    actividad_id = request.args.get("actividad_id", type=int)
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)

    if not actividad_id or not year or not month:
        return jsonify({"error": "actividad_id, year y month son requeridos"}), 400

    if month < 1 or month > 12:
        return jsonify({"error": "month inválido"}), 400

    if not Actividades.query.get(actividad_id):
        return jsonify({"error": "Actividad no encontrada"}), 404

    last_day = monthrange(year, month)[1]
    start = datetime(year, month, 1)
    end = datetime(year, month, last_day, 23, 59, 59)

    dates_with_classes = set()

    # 🌟 Incluimos días que tengan clases activas en el catálogo,
    # para permitir que se seleccionen también días con clases completas
    classes = Class.query.filter_by(id_actividad=actividad_id, estado=Class.STATUS_ACTIVE).filter(Class.fecha_hora >= start, Class.fecha_hora <= end).all()

    now = datetime.now()

    for class_obj in classes:
        if class_obj.fecha_hora and class_obj.fecha_hora <= now:
            continue

        if class_obj.fecha_hora:
            dates_with_classes.add(class_obj.fecha_hora.date().isoformat())

    return jsonify({"dates": sorted(dates_with_classes)}), 200

# ─── Rutas API: Gestión de Clases (Inscripciones de Alumnos) ───────────────────

@app.route("/api/classes/my", methods=["GET"])
def get_my_classes():
    current_user = _get_authenticated_user()
    if not current_user:
        return jsonify({"error": "No autenticado"}), 401

    current_datetime = _current_discount_datetime()
    now = current_datetime.replace(tzinfo=None) if getattr(current_datetime, "tzinfo", None) else current_datetime

    # 1. Traer inscripciones directas
    explicit_enrollments = Enrollment.query.filter_by(user_id=current_user.id).all()
    state_changed = False
    for enr in explicit_enrollments:
        state_changed = payment_service.recompute_enrollment_payment_state(enr, current_datetime) or state_changed
    if state_changed:
        db.session.commit()

    explicit_map = {enr.class_id: enr for enr in explicit_enrollments}
    
    # 2. Filtrar mensuales para desglosar el resto de sus clases implícitas
    monthly_enrollments = [enr for enr in explicit_enrollments if enr.tipo == ENROLLMENT_TYPE_MONTHLY and enr.estado in [Enrollment.STATUS_PENDING_PAYMENT, Enrollment.STATUS_PAID]]

    rooms = dict(db.session.execute(text("SELECT id, room FROM classes")).fetchall())

    my_classes = []
    
    for enr in explicit_enrollments:
        class_obj = enr.class_
        if not class_obj: continue
        # Ocultar clases que ya pasaron por más de un día
        if class_obj.fecha_hora and class_obj.fecha_hora < now - timedelta(days=1):
            continue
            
        my_classes.append({
            "class_id": class_obj.id,
            "class_name": class_obj.name,
            "actividad": class_obj.actividad.name if class_obj.actividad else class_obj.name,
            "fecha_hora": class_obj.fecha_hora.isoformat() if class_obj.fecha_hora else None,
            "estado_inscripcion": enr.estado,
            "estado_pago": enr.payment_status,
            "payment_status": enr.payment_status,
            "estado_clase": class_obj.estado,
            "tipo": enr.tipo,
            "enrollment_id": enr.id,
            "has_approved_payment": _has_approved_payment(enr),
            "is_implicit": False,
            "room": rooms.get(class_obj.id)
        })

    for enr in monthly_enrollments:
        class_obj = enr.class_
        if not class_obj or not class_obj.fecha_hora: continue
        
        month_start = datetime(class_obj.fecha_hora.year, class_obj.fecha_hora.month, 1)
        last_day = monthrange(class_obj.fecha_hora.year, class_obj.fecha_hora.month)[1]
        month_end = datetime(class_obj.fecha_hora.year, class_obj.fecha_hora.month, last_day, 23, 59, 59)
        
        # Buscar todas las clases subsecuentes del mes de la misma actividad
        implicit_classes = Class.query.filter(
            Class.id_actividad == class_obj.id_actividad,
            Class.fecha_hora > class_obj.fecha_hora,
            Class.fecha_hora <= month_end
        ).all()

        for ic in implicit_classes:
            if ic.fecha_hora.weekday() == class_obj.fecha_hora.weekday() and ic.fecha_hora.strftime("%H:%M") == class_obj.fecha_hora.strftime("%H:%M"):
                if ic.id in explicit_map:
                    continue
                
                if ic.fecha_hora < now - timedelta(days=1):
                    continue
                
                my_classes.append({
                    "class_id": ic.id,
                    "class_name": ic.name,
                    "actividad": ic.actividad.name if ic.actividad else ic.name,
                    "fecha_hora": ic.fecha_hora.isoformat(),
                    "estado_inscripcion": enr.estado,
                    "estado_pago": enr.payment_status,
                    "payment_status": enr.payment_status,
                    "estado_clase": ic.estado,
                    "tipo": "Mensual",
                    "enrollment_id": None,
                    "parent_enrollment_id": enr.id,
                    "has_approved_payment": _has_approved_payment(enr),
                    "is_implicit": True,
                    "room": rooms.get(ic.id)
                })

    my_classes.sort(key=lambda x: x["fecha_hora"] if x["fecha_hora"] else "")
    return jsonify({"classes": my_classes}), 200


@app.route("/api/classes/<int:class_id>/cancel-attendance", methods=["POST"])
def cancel_class_attendance(class_id):
    current_user = _get_authenticated_user()
    if not current_user:
        return jsonify({"error": "No autenticado"}), 401

    class_obj = Class.query.get(class_id)
    if not class_obj:
        return jsonify({"error": "Clase no encontrada"}), 404

    current_datetime = _current_discount_datetime()
    enrollment = Enrollment.query.filter_by(user_id=current_user.id, class_id=class_id).first()

    if enrollment:
        # Si la clase es explícita usamos el flujo común que ya tienen.
        enrollment_to_cancel = _shift_monthly_parent_if_needed(enrollment)
        result, error, status_code = cancellation_service.cancel_enrollment(enrollment_to_cancel, current_user, current_datetime)
        if error:
            return api_error(error, status_code)
        
        credit = result.get("credit")
        credit_generated = result.get("credit_generated")
    else:
        # Es una clase mensual implícita: debemos "materializarla" para poder cancelarla y liberar el cupo de ese día
        month_start = datetime(class_obj.fecha_hora.year, class_obj.fecha_hora.month, 1)
        last_day = monthrange(class_obj.fecha_hora.year, class_obj.fecha_hora.month)[1]
        month_end = datetime(class_obj.fecha_hora.year, class_obj.fecha_hora.month, last_day, 23, 59, 59)

        implicit_enrs = Enrollment.query.join(Class).filter(
            Enrollment.user_id == current_user.id,
            Enrollment.tipo == ENROLLMENT_TYPE_MONTHLY,
            Enrollment.estado.in_([Enrollment.STATUS_PENDING_PAYMENT, Enrollment.STATUS_PAID]),
            Class.id_actividad == class_obj.id_actividad,
            Class.fecha_hora >= month_start,
            Class.fecha_hora <= month_end
        ).all()

        parent_enr = None
        for enr in implicit_enrs:
            if enr.class_.fecha_hora.weekday() == class_obj.fecha_hora.weekday() and enr.class_.fecha_hora.strftime("%H:%M") == class_obj.fecha_hora.strftime("%H:%M"):
                if class_obj.fecha_hora > enr.class_.fecha_hora:
                    parent_enr = enr
                    break
        
        if not parent_enr:
            return jsonify({"error": "No estás inscripto en esta clase"}), 400

        enrollment = Enrollment(
            user_id=current_user.id,
            class_id=class_id,
            tipo=ENROLLMENT_TYPE_MONTHLY,
            estado=Enrollment.STATUS_CANCELLED,
            payment_status=parent_enr.payment_status,
            total_amount=0, paid_amount=0, remaining_amount=0, requiere_reembolso=False
        )
        db.session.add(enrollment)
        
        credit = None
        credit_generated = False
        
        if parent_enr.estado == Enrollment.STATUS_PAID:
            credit = _generate_credit_for_paid_enrollment(enrollment, class_obj, current_datetime)
            credit_generated = True

    try:
        db.session.commit()
    except Exception as err:
        db.session.rollback()
        logger.exception("[Cancelaciones] error al cancelar asistencia")
        return jsonify({"error": "Error interno al cancelar la asistencia"}), 500

    _promote_waitlist_for_class(class_obj)

    email_sent = False
    if credit:
        email_sent = send_credit_generated_email(enrollment.user, class_obj, credit)

    message = (
        "Te diste de baja del turno correctamente. Se te generó un crédito para futuras reservas."
        if credit_generated else "Te diste de baja del turno correctamente."
    )
    
    return api_success({
        "message": message, "class_id": class_obj.id, "credit_generated": credit_generated,
        "credit": credit_service.credit_payload(credit, current_datetime) if credit else None,
        "email_sent": email_sent
    }, message=message, status_code=200)

@app.route("/api/enrollments", methods=["POST"])
def create_enrollment():
    current_user = _get_authenticated_user()
    if not current_user:
        return jsonify({"error": "No autenticado"}), 401

    # Solo clientes pueden inscribirse a clases
    if current_user.role != "client":
        return api_error("Solo los clientes pueden inscribirse a clases", 403)

    data = request.get_json() or {}
    class_id = data.get("class_id")
    if not class_id:
        return api_error("Debe seleccionar una clase para inscribirse", 400)

    current_datetime = _current_discount_datetime()
    class_obj = Class.query.get(class_id)
    error, status_code = _validate_class_available_for_enrollment(class_obj, current_datetime)
    if error:
        return api_error(error, status_code)
        
    # 🌟 NUEVA VALIDACIÓN: Verificar si ya tiene una inscripción mensual que cubra esta clase en el mismo mes
    month_start = datetime(class_obj.fecha_hora.year, class_obj.fecha_hora.month, 1)
    last_day = monthrange(class_obj.fecha_hora.year, class_obj.fecha_hora.month)[1]
    month_end = datetime(class_obj.fecha_hora.year, class_obj.fecha_hora.month, last_day, 23, 59, 59)
    
    existing_monthly_enrs = Enrollment.query.join(Class).filter(
        Enrollment.user_id == current_user.id,
        Enrollment.tipo == ENROLLMENT_TYPE_MONTHLY,
        Enrollment.estado.in_([Enrollment.STATUS_PENDING_PAYMENT, Enrollment.STATUS_PAID]),
        Class.id_actividad == class_obj.id_actividad,
        Class.fecha_hora >= month_start,
        Class.fecha_hora <= month_end
    ).all()

    for enr in existing_monthly_enrs:
        if enr.class_id != class_obj.id and enr.class_.fecha_hora.weekday() == class_obj.fecha_hora.weekday() and enr.class_.fecha_hora.strftime("%H:%M") == class_obj.fecha_hora.strftime("%H:%M"):
            if data.get("tipo") == ENROLLMENT_TYPE_MONTHLY:
                return api_error("Ya te encuentras inscripto mensualmente en este horario y día de la semana para el mes actual.", 409)
            elif class_obj.fecha_hora >= enr.class_.fecha_hora:
                    # Verificar si canceló explícitamente esta clase
                    is_cancelled = Enrollment.query.filter_by(
                        user_id=current_user.id, class_id=class_obj.id
                    ).filter(Enrollment.estado.in_([Enrollment.STATUS_CANCELLED, "Cancelada", "cancelled"])).first()
                    if not is_cancelled:
                        return api_error("Esta clase ya está cubierta por tu suscripción mensual.", 409)

    enrollment_map = _enrollment_counts()

    # Eliminar de la lista de espera si se estaba inscribiendo con éxito
    WaitlistEntry.query.filter_by(user_id=current_user.id, class_id=class_obj.id).delete()

    existing_cancelled = Enrollment.query.filter_by(
        user_id=current_user.id,
        class_id=class_obj.id
    ).filter(
        Enrollment.estado.in_([Enrollment.STATUS_CANCELLED, Enrollment.STATUS_EXPIRED, "Cancelada", "cancelled"])
    ).first()

    if existing_cancelled:
        enrolled_count = enrollment_map.get(class_obj.id, 0)
        if enrolled_count >= (class_obj.cupoMaximo or 20):
            result = "full"
            enrollment = existing_cancelled
        else:
            existing_cancelled.estado = Enrollment.STATUS_PENDING_PAYMENT
            existing_cancelled.tipo = data.get("tipo", ENROLLMENT_TYPE_SINGLE)
            existing_cancelled.requiere_reembolso = False
            existing_cancelled.total_amount = 0
            existing_cancelled.paid_amount = 0
            existing_cancelled.remaining_amount = 0
            existing_cancelled.payment_status = ENROLLMENT_PAYMENT_STATUS_PENDING
            enrollment = existing_cancelled
            result = "new"
    else:
        enrollment, result = enrollment_service.create_or_reopen_enrollment(
            current_user,
            class_obj,
            data.get("tipo"),
            enrollment_map,
            current_datetime,
        )

    if result == "already_paid":
        db.session.commit()
        return api_error("Ya estás inscripto y pagaste esta clase", 409)
    if result == "full":
        if data.get("waitlist") or data.get("waitlist_type"):
            existing_enr = Enrollment.query.filter_by(
                user_id=current_user.id,
                class_id=class_obj.id
            ).filter(
                Enrollment.estado.in_([Enrollment.STATUS_PENDING_PAYMENT, Enrollment.STATUS_PAID])
            ).first()

            if existing_enr:
                return api_error("Ya estás inscripto en esta clase, no puedes unirte a la lista de espera", 400)

            waitlist_type = data.get("waitlist_type", WAITLIST_TYPE_INDIVIDUAL)
            waitlist_entry, waitlist_error = waitlist_service.add_waitlist_entry(
                current_user,
                class_obj,
                waitlist_type,
            )
            if waitlist_error:
                db.session.commit()
                return api_error(waitlist_error, 409)
            db.session.commit()
            return api_success({
                "message": "Te agregamos a la lista de espera",
                "waitlist": waitlist_entry.to_dict(),
            }, message="Te agregamos a la lista de espera", status_code=201)
        db.session.commit()
        return api_error("No quedan cupos disponibles para esta clase", 409)
    if result == "credit_used":
        credit = getattr(enrollment, "_used_credit", None)
        db.session.commit()
        return _credit_enrollment_response(enrollment, credit, current_datetime, 200)
    if result == "already_pending":
        db.session.commit()
        return api_success({
            "message": "Ya tenés una inscripción pendiente de pago",
            "enrollment": _enrollment_payload(enrollment, current_datetime),
            "payment_url": f"/pagos?tab=pending&enrollment_id={enrollment.id}",
        }, message="Ya tenés una inscripción pendiente de pago", status_code=200)
    if result == "new":
        db.session.add(enrollment)

    db.session.flush()
    credit = _available_credit_for_user_activity(current_user.id, class_obj.id_actividad, current_datetime)
    if credit:
        _consume_credit_for_enrollment(credit, enrollment, current_datetime)
        db.session.commit()
        return _credit_enrollment_response(enrollment, credit, current_datetime, 201)

    db.session.commit()
    return api_success({
        "message": "Inscripción creada. Podés completar el pago ahora o más adelante.",
        "enrollment": _enrollment_payload(enrollment, current_datetime),
        "payment_url": f"/pagos?tab=pending&enrollment_id={enrollment.id}",
    }, message="Inscripción creada. Podés completar el pago ahora o más adelante.", status_code=201)


@app.route("/api/waitlists", methods=["POST"])
def create_waitlist_entry():
    current_user = _get_authenticated_user()
    if not current_user:
        return jsonify({"error": "No autenticado"}), 401

    # Solo clientes pueden unirse a lista de espera
    if current_user.role != "client":
        return api_error("Solo los clientes pueden unirse a lista de espera", 403)

    data = request.get_json() or {}
    class_id = data.get("class_id")
    if not class_id:
        return api_error("Debe seleccionar una clase para lista de espera", 400)

    class_obj = Class.query.get(class_id)
    if not class_obj:
        return api_error("Clase no encontrada", 404)
        
    # 🌟 NUEVA VALIDACIÓN: Verificar si ya tiene una inscripción mensual que cubra esta clase en el mismo mes
    month_start = datetime(class_obj.fecha_hora.year, class_obj.fecha_hora.month, 1)
    last_day = monthrange(class_obj.fecha_hora.year, class_obj.fecha_hora.month)[1]
    month_end = datetime(class_obj.fecha_hora.year, class_obj.fecha_hora.month, last_day, 23, 59, 59)
    
    existing_monthly_enrs = Enrollment.query.join(Class).filter(
        Enrollment.user_id == current_user.id,
        Enrollment.tipo == ENROLLMENT_TYPE_MONTHLY,
        Enrollment.estado.in_([Enrollment.STATUS_PENDING_PAYMENT, Enrollment.STATUS_PAID]),
        Class.id_actividad == class_obj.id_actividad,
        Class.fecha_hora >= month_start,
        Class.fecha_hora <= month_end
    ).all()

    for enr in existing_monthly_enrs:
        if enr.class_id != class_obj.id and enr.class_.fecha_hora.weekday() == class_obj.fecha_hora.weekday() and enr.class_.fecha_hora.strftime("%H:%M") == class_obj.fecha_hora.strftime("%H:%M"):
            waitlist_type = data.get("type", WAITLIST_TYPE_INDIVIDUAL)
            if waitlist_type == WAITLIST_TYPE_MONTHLY:
                return api_error("Ya te encuentras inscripto mensualmente en este horario, por lo que no necesitas unirte a la lista de espera.", 409)
            elif class_obj.fecha_hora >= enr.class_.fecha_hora:
                    # Verificar si canceló explícitamente esta clase
                    is_cancelled = Enrollment.query.filter_by(
                        user_id=current_user.id, class_id=class_obj.id
                    ).filter(Enrollment.estado.in_([Enrollment.STATUS_CANCELLED, "Cancelada", "cancelled"])).first()
                    if not is_cancelled:
                        return api_error("Esta clase ya está cubierta por tu suscripción mensual.", 409)

    existing_enr = Enrollment.query.filter_by(
        user_id=current_user.id,
        class_id=class_obj.id
    ).filter(
        Enrollment.estado.in_([Enrollment.STATUS_PENDING_PAYMENT, Enrollment.STATUS_PAID])
    ).first()

    if existing_enr:
        return api_error("Ya estás inscripto en esta clase, no puedes unirte a la lista de espera", 400)

    waitlist_type = data.get("type", WAITLIST_TYPE_INDIVIDUAL)
    entry, error = waitlist_service.add_waitlist_entry(current_user, class_obj, waitlist_type)
    if error:
        return api_error(error, 400)

    db.session.commit()
    return api_success({
        "message": "Te agregamos a la lista de espera",
        "waitlist": entry.to_dict(),
    }, message="Te agregamos a la lista de espera", status_code=201)


@app.route("/api/enrollments/<int:enrollment_id>/cancel", methods=["POST"])
def cancel_enrollment(enrollment_id):
    current_user = _get_authenticated_user()
    if not current_user:
        return jsonify({"error": "No autenticado"}), 401

    enrollment = Enrollment.query.get(enrollment_id)
    enrollment_to_cancel = _shift_monthly_parent_if_needed(enrollment)
    current_datetime = _current_discount_datetime()
    result, error, status_code = cancellation_service.cancel_enrollment(enrollment_to_cancel, current_user, current_datetime)
    if error:
        return api_error(error, status_code)

    class_obj = result["class"]
    credit = result["credit"]

    try:
        db.session.commit()
    except Exception as err:
        db.session.rollback()
        logger.exception("[Cancelaciones] error enrollment_id=%s", enrollment_id)
        return jsonify({"error": "Error interno al procesar la cancelación", "details": str(err)}), 500

    email_sent = False
    if credit:
        email_sent = send_credit_generated_email(enrollment.user, class_obj, credit)

    _promote_waitlist_for_class(class_obj)

    message = (
        "Tu inscripción fue cancelada correctamente. Se generó un crédito para futuras reservas."
        if result["credit_generated"]
        else "Tu inscripción fue cancelada correctamente."
    )
    return api_success({
        "message": message,
        "enrollment_id": enrollment.id,
        "estado": enrollment.estado,
        "payment_status": enrollment.payment_status,
        "credit_generated": result["credit_generated"],
        "credit": credit_service.credit_payload(credit, current_datetime) if credit else None,
        "email_sent": email_sent,
        "pending_payments_expired": result["pending_payments_expired"],
    }, message=message, status_code=200)


@app.route("/api/enrollments/pending", methods=["GET"])
def pending_enrollments():
    current_user = _get_authenticated_user()
    if not current_user:
        return jsonify({"error": "No autenticado"}), 401

    if current_user.role != "client":
        return jsonify({"enrollments": []}), 200

    current_datetime = _discount_datetime_from_request()
    enrollments = (
        Enrollment.query
        .filter_by(user_id=current_user.id)
        .order_by(Enrollment.id.desc())
        .all()
    )

    changed = False
    pending = []
    for enrollment in enrollments:
        changed = _expire_enrollment_if_needed(enrollment, current_datetime) or changed
        changed = payment_service.recompute_enrollment_payment_state(enrollment, current_datetime) or changed
        if enrollment.estado == Enrollment.STATUS_PENDING_PAYMENT and float(enrollment.remaining_amount or 0) > 0:
            pending.append(_enrollment_payload(enrollment, current_datetime))

    if changed:
        db.session.commit()

    return jsonify({"enrollments": pending}), 200


@app.route("/api/credits/my", methods=["GET"])
def my_credits():
    current_user = _get_authenticated_user()
    if not current_user:
        return jsonify({"error": "No autenticado"}), 401

    if current_user.role != "client":
        return api_success({"credits": []}, status_code=200)

    current_datetime = _current_discount_datetime()
    credits = (
        Credit.query
        .filter_by(user_id=current_user.id)
        .order_by(Credit.expires_at.asc(), Credit.id.desc())
        .all()
    )
    payload = []
    for credit in credits:
        payload.append(credit_service.credit_payload(credit, current_datetime))

    return api_success({"credits": payload}, status_code=200)


@app.route("/api/notifications/my", methods=["GET"])
def my_notifications():
    current_user = _get_authenticated_user()
    if not current_user:
        return jsonify({"error": "No autenticado"}), 401

    notifications = notification_service.notifications_for_user(current_user.id)
    return api_success({"notifications": [notification.to_dict() for notification in notifications]}, status_code=200)


@app.route("/api/classes", methods=["POST"])
def create_class():
    data = request.get_json() or {}
    activity_id = data.get("activity_id")
    date_str = data.get("date")
    time_str = data.get("time")
    room = data.get("room")
    
    try:
        cupo_maximo = int(data.get("cupoMaximo", 20))
    except (ValueError, TypeError):
        cupo_maximo = 20

    if not activity_id or not date_str or not time_str or not room:
        return jsonify({"error": "Todos los campos son obligatorios (incluyendo el salón)"}), 400

    actividad = db.session.get(Actividades, activity_id)
    if not actividad:
        return jsonify({"error": "Actividad no encontrada"}), 404

    try:
        fecha_hora = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    except ValueError:
        return jsonify({"error": "Fecha u hora inválida"}), 400

    if fecha_hora < datetime.now():
        return jsonify({"error": "No se pueden crear clases en un horario que ya pasó"}), 400

    target_str = fecha_hora.strftime("%Y-%m-%d %H:%M")
    all_classes = Class.query.all()
    rooms = dict(db.session.execute(text("SELECT id, room FROM classes")).fetchall())
    
    existing_active_class = None
    room_conflict = None
    class_to_reactivate = None
    
    for c in all_classes:
        c_room = rooms.get(c.id)
        if c.fecha_hora and c.fecha_hora.strftime("%Y-%m-%d %H:%M") == target_str:
            is_active = getattr(c, "estado", Class.STATUS_ACTIVE) == Class.STATUS_ACTIVE
            
            if is_active:
                if c.id_actividad == actividad.id:
                    existing_active_class = c
                if c_room == room:
                    room_conflict = c
            else:
                if c.id_actividad == actividad.id:
                    class_to_reactivate = c
    
    if room_conflict:
        if room_conflict.id_actividad != actividad.id:
            return jsonify({"error": f"El {room} ya está ocupado por la clase '{room_conflict.name}' en ese horario"}), 400
            
    if existing_active_class:
        return jsonify({"error": "Ya existe una clase activa para esa actividad en ese horario"}), 400
        
    if class_to_reactivate:
        class_to_reactivate.estado = Class.STATUS_ACTIVE
        class_to_reactivate.cupoMaximo = cupo_maximo
        
        try:
            db.session.commit()
            db.session.execute(text("UPDATE classes SET room = :room WHERE id = :id"), {"room": room, "id": class_to_reactivate.id})
            db.session.commit()
            return jsonify({
                "message": "Clase reactivada correctamente en este horario",
                "class": {
                    "id": class_to_reactivate.id,
                    "name": class_to_reactivate.name,
                    "fecha_hora": class_to_reactivate.fecha_hora.isoformat(),
                    "activity_id": class_to_reactivate.id_actividad,
                    "room": room
                }
            }), 201
        except Exception as err:
            db.session.rollback()
            return jsonify({"error": f"Error interno al reactivar la clase: {str(err)}"}), 500

    new_class = Class(name=actividad.name, fecha_hora=fecha_hora, id_actividad=actividad.id, cupoMaximo=cupo_maximo)
    db.session.add(new_class)
    
    try:
        db.session.commit()
        db.session.execute(text("UPDATE classes SET room = :room WHERE id = :id"), {"room": room, "id": new_class.id})
        db.session.commit()
    except IntegrityError as err:
        db.session.rollback()
        return jsonify({"error": "Ya existe una clase para esa actividad en ese horario"}), 400
    except Exception as err:
        db.session.rollback()
        return jsonify({"error": f"Error interno: {str(err)}"}), 500

    return jsonify({
        "message": "Clase creada correctamente",
        "class": {
            "id": new_class.id,
            "name": new_class.name,
            "fecha_hora": new_class.fecha_hora.isoformat(),
            "activity_id": new_class.id_actividad,
            "room": room
        }
    }), 201

@app.route("/api/classes/<int:class_id>/discount", methods=["PUT"])
def apply_class_discount(class_id):
    current_user = _get_authenticated_user()
    if not current_user or current_user.role not in ["admin", "employee"]:
        return jsonify({"error": "No tienes permisos para aplicar descuentos"}), 403

    class_obj = Class.query.get(class_id)
    if not class_obj:
        return jsonify({"error": "Clase inexistente"}), 404
        
    
    # Aplicar a esta clase y a todas las futuras de la misma actividad, día de la semana y hora
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    related_classes = Class.query.filter(
        Class.id_actividad == class_obj.id_actividad,
        Class.fecha_hora >= today
    ).all()

    modified_count = 0
    for c in related_classes:
        if c.fecha_hora.weekday() == class_obj.fecha_hora.weekday() and c.fecha_hora.strftime("%H:%M") == class_obj.fecha_hora.strftime("%H:%M"):
            day = c.fecha_hora.day
            if 15 <= day <= 21:
                new_discount = 40
            elif day >= 22:
                new_discount = 70
            else:
                new_discount = 0
                
            if c.descuento != new_discount:
                c.descuento = new_discount
                modified_count += 1
            
    day = class_obj.fecha_hora.day
    obj_discount = 40 if 15 <= day <= 21 else (70 if day >= 22 else 0)
    
    if class_obj.descuento != obj_discount:
        class_obj.descuento = obj_discount
        if class_obj.fecha_hora < today:
            modified_count += 1

    db.session.commit()
    
    return jsonify({"message": "Descuento aplicado con éxito", "class": {"id": class_obj.id, "name": class_obj.name, "descuento": class_obj.descuento}}), 200

# ─── Rutas API: Asistencia QR (Compañero) ───────────────────────────────────

@app.route("/api/attendance/register", methods=["POST"])
def register_attendance():
    """Registra la asistencia de un usuario a una clase mediante QR."""
    data = request.get_json() or {}
    user_id = data.get("user_id")
    class_id = data.get("class_id")

    if not user_id or not class_id:
        return jsonify({"error": "user_id y class_id son requeridos"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuario Cards inexistente"}), 404

    class_obj = Class.query.get(class_id)
    if not class_obj:
        return jsonify({"error": "Clase inexistente"}), 404

    enrollment = Enrollment.query.filter_by(user_id=user_id, class_id=class_id).first()
    if not enrollment:
        month_start = datetime(class_obj.fecha_hora.year, class_obj.fecha_hora.month, 1)
        implicit_enr = Enrollment.query.join(Class).filter(
            Enrollment.user_id == user_id, Enrollment.tipo == ENROLLMENT_TYPE_MONTHLY,
            Class.id_actividad == class_obj.id_actividad, Class.fecha_hora >= month_start, Class.fecha_hora <= class_obj.fecha_hora
        ).all()
        
        valid_implicit = None
        for enr in implicit_enr:
            if enr.class_.fecha_hora.weekday() == class_obj.fecha_hora.weekday() and enr.class_.fecha_hora.strftime("%H:%M") == class_obj.fecha_hora.strftime("%H:%M"):
                valid_implicit = enr
                break
                
        if valid_implicit:
            enrollment = valid_implicit
        else:
            return jsonify({"error": "Usuario no está inscrito a la clase"}), 403

    if enrollment.estado != Enrollment.STATUS_PAID:
        return jsonify({"error": "La inscripción no está pagada"}), 403

    existing = Attendance.query.filter_by(user_id=user_id, class_id=class_id).first()
    if existing:
        return jsonify({"error": "Asistencia ya registrada"}), 409

    new_attendance = Attendance(user_id=user_id, class_id=class_id)
    db.session.add(new_attendance)
    db.session.commit()

    return jsonify({
        "message": "Asistencia registrada correctamente", 
        "attendance": {
            "id": new_attendance.id,
            "user_id": new_attendance.user_id,
            "class_id": new_attendance.class_id,
            "created_at": new_attendance.created_at.isoformat()
        }
    }), 201


@app.route("/api/classes/<int:class_id>/attendance", methods=["GET"])
def get_class_attendance(class_id):
    """Devuelve la lista de asistencia de una clase para consulta del staff."""
    current_user = _get_authenticated_user()
    if not current_user:
        return jsonify({"error": "No autenticado"}), 401
    if current_user.role not in ["admin", "employee"]:
        return jsonify({"error": "No tienes permisos para consultar asistencias"}), 403

    class_obj = Class.query.get(class_id)
    if not class_obj:
        return jsonify({"error": "Clase inexistente"}), 404

    attendances = (
        Attendance.query
        .filter_by(class_id=class_id)
        .order_by(Attendance.created_at.desc())
        .all()
    )
    attended_by_user_id = {attendance.user_id: attendance for attendance in attendances}

    paid_enrollments_direct = (
        Enrollment.query
        .filter_by(class_id=class_id, estado=Enrollment.STATUS_PAID)
        .all()
    )
    
    month_start = datetime(class_obj.fecha_hora.year, class_obj.fecha_hora.month, 1)
    implicit_enrs = Enrollment.query.join(Class).filter(
        Enrollment.tipo == ENROLLMENT_TYPE_MONTHLY,
        Enrollment.estado == Enrollment.STATUS_PAID,
        Class.id_actividad == class_obj.id_actividad,
        Class.fecha_hora >= month_start,
        Class.fecha_hora < class_obj.fecha_hora
    ).all()
    
    paid_enrollments_map = {enr.user_id: enr for enr in paid_enrollments_direct}
    for enr in implicit_enrs:
        if enr.class_.fecha_hora.weekday() == class_obj.fecha_hora.weekday() and enr.class_.fecha_hora.strftime("%H:%M") == class_obj.fecha_hora.strftime("%H:%M"):
            if enr.user_id not in paid_enrollments_map:
                paid_enrollments_map[enr.user_id] = enr
                
    users = [User.query.get(uid) for uid in paid_enrollments_map.keys()]
    users.sort(key=lambda u: (u.apellido or "", u.username or ""))

    roster = []
    for user in users:
        attendance = attended_by_user_id.get(user.id)
        roster.append({
            "user_id": user.id,
            "username": user.username,
            "apellido": user.apellido,
            "email": user.email,
            "present": attendance is not None,
            "attendance_id": attendance.id if attendance else None,
            "attendance_created_at": attendance.created_at.isoformat() if attendance and attendance.created_at else None,
        })

    total_paid = len(users)

    return jsonify({
        "class": _class_slot_payload(class_obj, total_paid),
        "summary": {
            "present": len(attendances),
            "paid_enrollments": total_paid,
            "pending": max(total_paid - len(attendances), 0),
        },
        "attendances": [
            {
                "id": attendance.id,
                "user_id": attendance.user.id,
                "username": attendance.user.username,
                "apellido": attendance.user.apellido,
                "email": attendance.user.email,
                "created_at": attendance.created_at.isoformat() if attendance.created_at else None,
            }
            for attendance in attendances
        ],
        "roster": roster,
    }), 200

# ─── Rutas API: Gestión de Cancelaciones por Staff (US #19) ───────────────────

@app.route("/api/classes/<int:clase_id>/cancelar", methods=["POST"])
def cancelar_clase_staff(clase_id):
    """US #19: El profesor o administrador cancela una clase completa.
    Marca la clase como cancelada y libera el horario para nuevas asignaciones.
    """
    user_id_sesion = session.get("user_id")
    if not user_id_sesion:
        return jsonify({"error": "No autenticado"}), 401

    current_user = User.query.get(user_id_sesion)
    if not current_user or current_user.role not in ["admin", "employee"]:
        return jsonify({"error": "No tienes permisos de personal para cancelar clases"}), 403

    class_obj = Class.query.get_or_404(clase_id)
    
    if class_obj.estado == Class.STATUS_CANCELLED:
        return jsonify({"error": "Esta clase ya fue cancelada"}), 400

    current_datetime = _current_discount_datetime()
    
    _materialize_implicit_enrollments_for_cancellation(class_obj)

    # Obtenemos los usuarios que realmente estaban activos (no cancelados previamente)
    active_user_ids = {
        enr.user_id for enr in Enrollment.query.filter_by(class_id=clase_id).filter(
            Enrollment.estado.notin_([Enrollment.STATUS_CANCELLED, "Cancelada", "cancelled"])
        ).all()
    }

    cancellation = cancellation_service.cancel_class(class_obj, current_datetime)

    try:
        db.session.commit()
    except Exception as err:
        db.session.rollback()
        logger.exception("[Cancelaciones] error class_id=%s", clase_id)
        return jsonify({"error": "Error interno al procesar la cancelación", "details": str(err)}), 500

    # Filtramos los correos solo para los usuarios que estaban activos
    valid_email_jobs = [
        (u.id, c.id, cred.id if cred else None)
        for u, c, cred in cancellation.get("email_jobs", [])
        if u.id in active_user_ids
    ]

    def send_emails_async(app_obj, jobs):
        with app_obj.app_context():
            for uid, cid, cred_id in jobs:
                u = User.query.get(uid)
                c = Class.query.get(cid)
                cred = Credit.query.get(cred_id) if cred_id else None
                if not u or not c:
                    continue
                send_class_cancelled_email(u, c, credit_generated=cred is not None)
                if cred:
                    send_credit_generated_email(u, c, cred)

    # Enviamos los correos en un hilo de fondo para que no demore la respuesta del servidor
    from flask import current_app
    app_obj = current_app._get_current_object()
    threading.Thread(target=send_emails_async, args=(app_obj, valid_email_jobs)).start()

    return jsonify({
        "message": f"Clase '{class_obj.name}' cancelada exitosamente. El turno fue liberado en el calendario.",
        "class_id": clase_id,
        "class_name": class_obj.name,
        "estado": Class.STATUS_CANCELLED,
        "credits_created": cancellation["credits_created"],
        "notifications_created": cancellation["notifications_created"],
        "emails_sent": len(valid_email_jobs),
    }), 200


@app.route("/api/settings/notification-message", methods=["GET"])
def get_notification_message():
    current_user = _get_authenticated_user()
    if not current_user:
        return jsonify({"error": "No autenticado"}), 401
    if current_user.role != "admin":
        return jsonify({"error": "No tienes permisos para acceder a esta configuración"}), 403

    setting = SystemSetting.query.filter_by(key="cancellation_notification_message").first()
    return jsonify({"message": setting.value if setting else ""}), 200


@app.route("/api/settings/notification-message", methods=["PUT"])
def update_notification_message():
    current_user = _get_authenticated_user()
    if not current_user:
        return jsonify({"error": "No autenticado"}), 401
    if current_user.role != "admin":
        return jsonify({"error": "No tienes permisos para modificar esta configuración"}), 403

    data = request.get_json() or {}
    message = data.get("message", "")
    if not isinstance(message, str) or not message.strip():
        return jsonify({"error": "El mensaje es obligatorio"}), 400

    trimmed_message = message.strip()
    setting = SystemSetting.query.filter_by(key="cancellation_notification_message").first()
    if not setting:
        setting = SystemSetting(key="cancellation_notification_message", value=trimmed_message)
        db.session.add(setting)
    else:
        setting.value = trimmed_message

    try:
        db.session.commit()
    except Exception as err:
        db.session.rollback()
        return jsonify({"error": "Error interno al guardar la configuración", "details": str(err)}), 500

    return jsonify({"message": "Mensaje de notificación actualizado correctamente", "notification_message": setting.value}), 200


# ─── Rutas API: Pasarela de Pagos (Mercado Pago) ──────────────────────────────

@app.route("/api/payments/history", methods=["GET"])
def get_payment_history():
    current_user = _get_authenticated_user()
    if not current_user:
        return jsonify({"error": "No autenticado"}), 401

    # Los clientes ven su propio historial. Admins/empleados ven todos.
    if current_user.role == "client":
        payments = Payment.query.filter_by(user_id=current_user.id).order_by(Payment.created_at.desc()).all()
    else:
        payments = Payment.query.order_by(Payment.created_at.desc()).all()

    return jsonify({"payments": [p.to_dict() for p in payments]}), 200


@app.route("/api/admin/enrollments/payments", methods=["GET"])
def get_admin_payment_enrollments():
    current_user = _get_authenticated_user()
    if not current_user or current_user.role not in ["admin", "employee"]:
        return jsonify({"error": "No tienes permisos"}), 403

    # El reporte necesita todos los pagos aprobados para generar gráficos y tablas.
    payments = Payment.query.filter(Payment.status == Payment.STATUS_APPROVED).order_by(Payment.created_at.desc()).all()
    
    payload = []
    for p in payments:
        payment_dict = p.to_dict()
        user = p.user
        if user:
            payment_dict['user_username'] = user.username
            payment_dict['user_apellido'] = user.apellido
            payment_dict['user_email'] = user.email
            payment_dict['user'] = {
                "username": user.username,
                "apellido": user.apellido,
                "email": user.email
            }
            
            act_name = "-"
            class_obj = None
            if p.enrollment and p.enrollment.class_:
                class_obj = p.enrollment.class_
            elif getattr(p, "class_", None):
                class_obj = p.class_
            if class_obj:
                act_name = class_obj.actividad.name if getattr(class_obj, "actividad", None) else class_obj.name
            payment_dict['actividad'] = act_name

        payload.append(payment_dict)

    return jsonify({"payments": payload}), 200


@app.route("/api/payments/create", methods=["POST"])
def create_payment():
    request_start = time.perf_counter()
    timings = {}

    def finish_timing(outcome):
        timings["db_queries"] = getattr(g, "payment_query_count", 0)
        timings["db_query_time"] = round(getattr(g, "payment_query_ms", 0.0), 2)
        timings["total_request"] = _elapsed_ms(request_start)
        logger.info(
            "[PAYMENT_TIMING] outcome=%s %s",
            outcome,
            " ".join(f"{key}={value}ms" if isinstance(value, float) else f"{key}={value}" for key, value in timings.items()),
        )

    current_user = _get_authenticated_user()
    if not current_user:
        finish_timing("unauthenticated")
        return jsonify({"error": "No autenticado"}), 401

    parse_start = time.perf_counter()
    data = request.get_json() or {}
    payment_method = data.get("payment_method", Payment.METHOD_MERCADO_PAGO)
    enrollment_id = data.get("enrollment_id")
    requested_payment_type = data.get("payment_type", PAYMENT_TYPE_FULL)
    timings["parse_request"] = _elapsed_ms(parse_start)

    if payment_method not in Payment.VALID_PAYMENT_METHODS:
        finish_timing("invalid_payment_method")
        return jsonify({"error": "Método de pago inválido"}), 400

    if requested_payment_type not in Payment.VALID_PAYMENT_TYPES:
        finish_timing("invalid_payment_type")
        return jsonify({"error": "Tipo de pago inválido"}), 400

    if payment_method != Payment.METHOD_MERCADO_PAGO:
        finish_timing("invalid_gateway")
        return jsonify({"error": "Por ahora solo está disponible Mercado Pago Checkout Pro"}), 400

    if not enrollment_id:
        finish_timing("missing_enrollment")
        return jsonify({"error": "Debe seleccionar una inscripción pendiente para pagar"}), 400

    enrollment_query_start = time.perf_counter()
    enrollment = Enrollment.query.get(enrollment_id)
    timings["load_enrollment"] = _elapsed_ms(enrollment_query_start)
    current_datetime = _current_discount_datetime()
    validate_start = time.perf_counter()
    error, status_code = _validate_enrollment_payable(enrollment, current_user, current_datetime)
    timings["validate_enrollment"] = _elapsed_ms(validate_start)
    if error:
        finish_timing("validation_error")
        return jsonify({"error": error}), status_code

    calculate_start = time.perf_counter()
    class_obj = enrollment.class_
    product_type = _payment_type_for_enrollment(enrollment)

    quote = payment_service.enrollment_payment_quote(enrollment, current_datetime)
    discount_percentage = int(quote.get("discount_percentage", 0))

    if product_type == "single_class" or enrollment.tipo == ENROLLMENT_TYPE_SINGLE:
        amount = 3000.0
    else:
        amount = _get_monthly_base_price(class_obj)

    full_final_amount = _calculate_final_amount(amount, discount_percentage)
    timings["calculate_amounts"] = _elapsed_ms(calculate_start)
    if not float(enrollment.paid_amount or 0):
        enrollment.total_amount = round(full_final_amount, 2)
    else:
        enrollment.total_amount = float(enrollment.total_amount or 0) or round(full_final_amount, 2)
    recompute_start = time.perf_counter()
    payment_service.recompute_enrollment_payment_state(enrollment, current_datetime)
    timings["recompute"] = _elapsed_ms(recompute_start)
    remaining_amount = float(enrollment.remaining_amount or 0)
    if requested_payment_type == PAYMENT_TYPE_FULL and float(enrollment.paid_amount or 0) > 0:
        requested_payment_type = PAYMENT_TYPE_BALANCE

    if remaining_amount <= 0:
        enrollment.estado = Enrollment.STATUS_PAID
        recompute_start = time.perf_counter()
        payment_service.recompute_enrollment_payment_state(enrollment, current_datetime)
        timings["recompute"] = round(timings.get("recompute", 0) + _elapsed_ms(recompute_start), 2)
        commit_start = time.perf_counter()
        db.session.commit()
        timings["commit"] = _elapsed_ms(commit_start)
        finish_timing("already_paid")
        return jsonify({"error": "La inscripción ya está pagada"}), 409

    payment_amounts_start = time.perf_counter()
    amount, final_amount = payment_service.payment_amounts_for_type(
        enrollment,
        requested_payment_type,
        amount,
        full_final_amount,
    )
    timings["payment_amounts_for_type"] = _elapsed_ms(payment_amounts_start)

    if final_amount <= 0:
        finish_timing("no_pending_balance")
        return jsonify({"error": "No hay saldo pendiente para este tipo de pago"}), 400
    if final_amount > remaining_amount + 0.01:
        finish_timing("overpay")
        return jsonify({"error": "El pago supera el saldo pendiente"}), 400

    log_discount_start = time.perf_counter()
    _log_discount_quote(current_datetime, class_obj, discount_percentage, amount, final_amount)
    timings["log_discount"] = _elapsed_ms(log_discount_start)

    create_record_start = time.perf_counter()
    payment = payment_service.reusable_pending_payment(
        enrollment.id,
        current_user.id,
        payment_method,
        requested_payment_type,
    )
    reused_payment = payment is not None
    if payment:
        payment_service.prepare_payment_for_checkout(
            payment,
            product_type,
            requested_payment_type,
            payment_method,
            amount,
            discount_percentage,
            final_amount,
            current_datetime,
        )
    else:
        payment = Payment(
            user_id=current_user.id,
            enrollment_id=enrollment.id,
            product_type=product_type,
            payment_type=requested_payment_type,
            payment_method=payment_method,
            amount=amount,
            discount_percentage=discount_percentage,
            final_amount=final_amount,
            status=Payment.STATUS_PENDING,
        )
        db.session.add(payment)
        db.session.flush()
    payment_service.expire_equivalent_pending_payments(payment)
    timings["reuse_payment_record" if reused_payment else "create_payment_record"] = _elapsed_ms(create_record_start)

    preference_payload_start = time.perf_counter()
    activity_name = class_obj.actividad.name if class_obj.actividad else class_obj.name
    title = f"Suscripción mensual - {activity_name}" if product_type == "monthly_subscription" else f"Clase individual - {activity_name}"
    if requested_payment_type == PAYMENT_TYPE_DEPOSIT:
        title = f"Seña - {title}"
    elif requested_payment_type == PAYMENT_TYPE_BALANCE:
        title = f"Saldo - {title}"
    preference_data = {
        "items": [
            {
                "title": title,
                "quantity": 1,
                "unit_price": float(final_amount),
                "currency_id": "ARS",
            }
        ],
        "payer": _mercado_pago_payer_payload(current_user),
        "external_reference": str(payment.id),
        "back_urls": {
            "success": _mercado_pago_callback_url(
                "PAYMENT_SUCCESS_URL",
                "/api/payments/return/success",
                "http://localhost:5000/api/payments/return/success",
            ),
            "failure": _mercado_pago_callback_url(
                "PAYMENT_FAILURE_URL",
                "/api/payments/return/failure",
                "http://localhost:5000/api/payments/return/failure",
            ),
            "pending": _mercado_pago_callback_url(
                "PAYMENT_PENDING_URL",
                f"/api/payments/return/{PAYMENT_RETURN_STATUS_PENDING}",
                f"http://localhost:5000/api/payments/return/{PAYMENT_RETURN_STATUS_PENDING}",
            ),
        },
        "notification_url": _mercado_pago_notification_url(),
        "auto_return": "approved",
    }
    timings["build_preference_payload"] = _elapsed_ms(preference_payload_start)

    validate_urls_start = time.perf_counter()
    back_urls_error = _validate_mercado_pago_back_urls(preference_data)
    timings["validate_back_urls"] = _elapsed_ms(validate_urls_start)
    if back_urls_error:
        logger.error("[MercadoPago] back_urls_invalidas error=%s payload=%s", back_urls_error, preference_data)
        db.session.rollback()
        finish_timing("invalid_back_urls")
        return jsonify({"error": f"Configuración inválida de Mercado Pago: {back_urls_error}"}), 500

    try:
        mp_start = time.perf_counter()
        _log_mercado_pago_payload(preference_data)
        preference_result = get_mercadopago_client().preference().create(preference_data)
        _log_mercado_pago_response(preference_result)
        timings["mercadopago_preference"] = _elapsed_ms(mp_start)
    except RuntimeError as err:
        logger.exception("[MercadoPago] configuracion_invalida")
        db.session.rollback()
        timings["mercadopago_preference"] = _elapsed_ms(mp_start)
        finish_timing("mercadopago_config_error")
        return jsonify({"error": str(err)}), 500
    except Exception as err:
        logger.exception("[MercadoPago] sdk_error")
        db.session.rollback()
        timings["mercadopago_preference"] = _elapsed_ms(mp_start)
        finish_timing("mercadopago_sdk_error")
        return jsonify({"error": f"Error del SDK de Mercado Pago: {str(err)}"}), 502

    if not isinstance(preference_result, dict):
        logger.error("[MercadoPago] respuesta_invalida response=%s", preference_result)
        db.session.rollback()
        finish_timing("mercadopago_invalid_response")
        return jsonify({"error": "Mercado Pago devolvió una respuesta inválida"}), 502

    if preference_result.get("status") not in [200, 201]:
        logger.error("[MercadoPago] preferencia_rechazada response=%s", preference_result)
        db.session.rollback()
        response_body = preference_result.get("response") or {}
        mp_message = response_body.get("message") or response_body.get("error") or "Error del servidor de pagos"
        finish_timing("mercadopago_rejected")
        return jsonify({"error": f"Mercado Pago rechazó la preferencia: {mp_message}"}), 502

    preference_response = preference_result.get("response", {})
    if not isinstance(preference_response, dict):
        logger.error("[MercadoPago] body_invalido body=%s response=%s", preference_response, preference_result)
        db.session.rollback()
        finish_timing("mercadopago_invalid_body")
        return jsonify({"error": "Mercado Pago no devolvió un body válido"}), 502

    parse_mp_start = time.perf_counter()
    init_point = _mercado_pago_checkout_url(preference_response)
    preference_id = preference_response.get("id")
    timings["parse_mercadopago_response"] = _elapsed_ms(parse_mp_start)
    logger.info(
        "[MercadoPago] preferencia_creada payment_id=%s preference_id=%s checkout_url=%s",
        payment.id,
        preference_id,
        init_point,
    )

    if not init_point:
        logger.error("[MercadoPago] init_point_faltante response=%s", preference_result)
        db.session.rollback()
        finish_timing("missing_init_point")
        return jsonify({"error": "Mercado Pago no devolvió init_point para el checkout"}), 502

    if not preference_id:
        logger.error("[MercadoPago] preference_id_faltante response=%s", preference_result)
        db.session.rollback()
        finish_timing("missing_preference_id")
        return jsonify({"error": "Mercado Pago no devolvió id de preferencia"}), 502

    commit_start = time.perf_counter()
    payment.mercado_pago_preference_id = preference_id
    db.session.commit()
    timings["commit"] = _elapsed_ms(commit_start)

    response_start = time.perf_counter()
    response_payload = {
        "payment_id": payment.id,
        "enrollment_id": enrollment.id,
        "init_point": init_point,
        "preference_id": preference_id,
        "amount": amount,
        "discount_percentage": discount_percentage,
        "final_amount": final_amount,
        "payment_type": payment.payment_type,
        "product_type": payment.product_type,
        "remaining_amount": enrollment.remaining_amount,
    }
    timings["build_response"] = _elapsed_ms(response_start)
    finish_timing("success")
    return jsonify({
        **response_payload,
    }), 200


@app.route("/api/payments/return/<result>", methods=["GET"])
def mercado_pago_return(result):
    logger.info("[MercadoPago Callback] result=%s query=%s", result, request.args.to_dict())
    current_datetime = _current_discount_datetime()
    payment_reference = request.args.get("external_reference")
    preference_id = request.args.get("preference_id")
    mercado_pago_payment_id = request.args.get("payment_id") or request.args.get("collection_id")
    mercado_pago_status = request.args.get("status") or request.args.get("collection_status")
    status_detail = request.args.get("status_detail")

    payment = None
    if payment_reference:
        payment = Payment.query.get(payment_reference)
    if not payment and preference_id:
        payment = Payment.query.filter_by(mercado_pago_preference_id=preference_id).first()

    if not payment:
        logger.error("[MercadoPago Callback] payment_no_encontrado")
        return redirect(_frontend_payments_url(PAYMENT_RETURN_STATUS_FAILURE, "Error del servidor de pagos"))

    if mercado_pago_payment_id:
        payment.mercado_pago_payment_id = str(mercado_pago_payment_id)
        mp_payment = _mercado_pago_payment_response(mercado_pago_payment_id)
        if mp_payment:
            mercado_pago_status = mp_payment.get("status") or mercado_pago_status
            status_detail = mp_payment.get("status_detail") or status_detail

    if mercado_pago_status:
        redirect_status, message = _apply_mercado_pago_status(
            payment,
            mercado_pago_status,
            status_detail,
            mercado_pago_payment_id,
            current_datetime,
        )
    elif result == PAYMENT_RETURN_STATUS_SUCCESS:
        redirect_status, message = _apply_mercado_pago_status(
            payment,
            MERCADO_PAGO_STATUS_APPROVED,
            status_detail,
            mercado_pago_payment_id,
            current_datetime,
        )
    elif result == PAYMENT_RETURN_STATUS_PENDING:
        redirect_status, message = _apply_mercado_pago_status(
            payment,
            MERCADO_PAGO_STATUS_PENDING,
            status_detail,
            mercado_pago_payment_id,
            current_datetime,
        )
    else:
        redirect_status, message = _apply_mercado_pago_status(
            payment,
            None,
            status_detail,
            mercado_pago_payment_id,
            current_datetime,
        )

    db.session.commit()
    logger.info(
        "[MercadoPago Callback] payment_id=%s status=%s redirect_status=%s",
        payment.id,
        payment.status,
        redirect_status,
    )
    return redirect(_frontend_payments_url(redirect_status, message))


@app.route("/api/payments/webhook", methods=["POST", "GET"])
def mercado_pago_webhook():
    payload = request.get_json(silent=True) or {}
    query = request.args.to_dict()
    logger.info("[MercadoPago Webhook] query=%s payload=%s", query, payload)

    topic = query.get("topic") or query.get("type") or payload.get("type")

    if topic in ["payment", "merchant_order"]:
        payment_id = query.get("data.id") or query.get("id") or (payload.get("data") or {}).get("id")
        if payment_id:
            mp_payment = _mercado_pago_payment_response(payment_id)
            if mp_payment:
                payment = _payment_from_mercado_pago_response(mp_payment)
                if payment:
                    current_datetime = _current_discount_datetime()
                    _apply_mercado_pago_status(
                        payment,
                        mp_payment.get("status"),
                        mp_payment.get("status_detail"),
                        payment_id,
                        current_datetime,
                    )
                    db.session.commit()

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "0").lower() in {"1", "true", "yes", "on"}
    app.run(debug=debug, host="0.0.0.0", port=port)
