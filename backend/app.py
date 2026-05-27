import os
import logging
import random
from datetime import datetime, timedelta
from calendar import monthrange
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from dotenv import load_dotenv

from flask import Flask, request, jsonify, session, redirect
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

try:
    from email_service import send_admin_login_code, send_class_cancelled_email, send_credit_generated_email
    from mercadopago_config import get_mercadopago_client
    from models import db, User
    # Importar todos los modelos requeridos
    from models import Class, Enrollment, Attendance, Actividades, Credit, Credito, Notification, Payment, SystemSetting
    from constants import (
        DISCOUNT_PERCENTAGES,
        ENROLLMENT_STATUS_PENDING_PAYMENT,
        ENROLLMENT_TYPE_SINGLE,
        ENROLLMENT_TYPE_MONTHLY,
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
    from services import cancellation_service, class_service, credit_service, enrollment_service, notification_service, payment_service
    from services.api_response import api_error, api_success
except ModuleNotFoundError:
    from .email_service import send_admin_login_code, send_class_cancelled_email, send_credit_generated_email
    from .mercadopago_config import get_mercadopago_client
    from .models import db, User
    # Importar todos los modelos requeridos
    from .models import Class, Enrollment, Attendance, Actividades, Credit, Credito, Notification, Payment, SystemSetting
    from .constants import (
        DISCOUNT_PERCENTAGES,
        ENROLLMENT_STATUS_PENDING_PAYMENT,
        ENROLLMENT_TYPE_SINGLE,
        ENROLLMENT_TYPE_MONTHLY,
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
    from .services import cancellation_service, class_service, credit_service, enrollment_service, notification_service, payment_service
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

# Inicializa extensiones
db.init_app(app)

# CORS para frontend local Vue/Vite
CORS(
    app,
    supports_credentials=True,
    origins=[
        "http://localhost:5173",
        "http://localhost:5174"
    ]
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
    
    for enr in monthly_enrollments:
        base_class = enr.class_
        y = base_class.fecha_hora.year
        m = base_class.fecha_hora.month
        end = datetime(y, m, monthrange(y, m)[1], 23, 59, 59)
        
        subsequent_classes = Class.query.filter(Class.id_actividad == base_class.id_actividad, Class.fecha_hora > base_class.fecha_hora, Class.fecha_hora <= end, Class.estado == Class.STATUS_ACTIVE).all()
        for c in subsequent_classes:
            if c.fecha_hora.weekday() == base_class.fecha_hora.weekday() and c.fecha_hora.strftime("%H:%M") == base_class.fecha_hora.strftime("%H:%M"):
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
    discount = int(enrollment.class_.descuento or 0)
    
    if enrollment.tipo == ENROLLMENT_TYPE_SINGLE:
        amount = float(quote.get("amount", 0))
    else:
        amount = _get_monthly_base_price(enrollment.class_)
        
    quote["amount"] = amount
    quote["discount_percentage"] = discount
    quote["final_amount"] = amount - (amount * discount / 100)
    return quote


def _enrollment_payload(enrollment, current_datetime=None):
    payload = enrollment_service.enrollment_payload(enrollment, current_datetime)
    discount = int(enrollment.class_.descuento or 0)
    
    if enrollment.tipo == ENROLLMENT_TYPE_SINGLE:
        amount = 3000.0
    else:
        amount = _get_monthly_base_price(enrollment.class_)
        
    payload["amount"] = amount
    payload["discount_percentage"] = discount
    payload["final_amount"] = amount - (amount * discount / 100)
    if not float(payload.get("total_amount") or 0):
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
    if not email:
        return jsonify({"error": "Debe ingresar un email"}), 400

    user = User.query.filter_by(email=email, role="admin").first()
    if not user:
        return jsonify({"error": "Email no corresponde a un administrador"}), 401

    code = f"{random.randint(0, 999999):06d}"
    session["admin_login_email"] = email
    session["admin_login_code"] = code
    session["admin_login_code_expires_at"] = (datetime.utcnow() + timedelta(minutes=5)).timestamp()

    send_admin_login_code(user, code)
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
        return jsonify({"error": "Código incorrecto o email no coincide"}), 401

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
        "user": {"id": user.id, "username": user.username, "email": user.email, "role": user.role}
    }), 200

# ─── Rutas API: Actividades, Usuarios y Catálogo ────────────────────────────────────────

@app.route("/api/actividades", methods=["GET"])
def get_actividades():
    actividades = Actividades.query.all()
    return jsonify([{"id": ac.id, "name": ac.name} for ac in actividades]), 200


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
    # 🌟 FILTRADO SEGURO: Enviamos al frontend únicamente las clases activas
    classes = Class.query.filter_by(id_actividad=actividad_id, estado=Class.STATUS_ACTIVE).all()
    return jsonify({
        "classes": [{"id": c.id, "fecha_hora": c.fecha_hora.isoformat(), "time": c.fecha_hora.strftime("%H:%M")} for c in classes]
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
    available_slots = []
    full_count = 0

    # 🌟 Traemos solo las clases activas para que no bloqueen horarios en el catálogo
    classes = Class.query.filter_by(id_actividad=actividad_id, estado=Class.STATUS_ACTIVE).filter(db.func.date(Class.fecha_hora) == day).order_by(Class.fecha_hora).all()

    now = datetime.now()

    for class_obj in classes:
        if class_obj.fecha_hora and class_obj.fecha_hora <= now:
            continue
            
        enrolled_count = enrollment_map.get(class_obj.id, 0)
        slot = _class_slot_payload(class_obj, enrolled_count)
        if slot["available_spots"] > 0:
            available_slots.append(slot)
        else:
            full_count += 1

    return jsonify({"actividad": actividad.name, "fecha": fecha, "available": available_slots, "full_count": full_count}), 200


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

    enrollment_map = _enrollment_counts()
    dates_with_cupo = set()

    # 🌟 Consideramos solo las clases activas para marcar los días con disponibilidad
    classes = Class.query.filter_by(id_actividad=actividad_id, estado=Class.STATUS_ACTIVE).filter(Class.fecha_hora >= start, Class.fecha_hora <= end).all()

    now = datetime.now()

    for class_obj in classes:
        if class_obj.fecha_hora and class_obj.fecha_hora <= now:
            continue

        enrolled_count = enrollment_map.get(class_obj.id, 0)
        cupo_max = class_obj.cupoMaximo if class_obj.cupoMaximo is not None else 20
        if enrolled_count < cupo_max:
            dates_with_cupo.add(class_obj.fecha_hora.date().isoformat())

    return jsonify({"dates": sorted(dates_with_cupo)}), 200

# ─── Rutas API: Gestión de Clases (Inscripciones de Alumnos) ───────────────────

@app.route("/api/enrollments", methods=["POST"])
def create_enrollment():
    current_user = _get_authenticated_user()
    if not current_user:
        return jsonify({"error": "No autenticado"}), 401

    data = request.get_json() or {}
    class_id = data.get("class_id")
    if not class_id:
        return api_error("Debe seleccionar una clase para inscribirse", 400)

    current_datetime = _current_discount_datetime()
    class_obj = Class.query.get(class_id)
    error, status_code = _validate_class_available_for_enrollment(class_obj, current_datetime)
    if error:
        return api_error(error, status_code)

    enrollment_map = _enrollment_counts()
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


@app.route("/api/enrollments/pending", methods=["GET"])
def pending_enrollments():
    current_user = _get_authenticated_user()
    if not current_user:
        return jsonify({"error": "No autenticado"}), 401

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
    
    try:
        cupo_maximo = int(data.get("cupoMaximo", 20))
    except (ValueError, TypeError):
        cupo_maximo = 20

    if not activity_id or not date_str or not time_str:
        return jsonify({"error": "Todos los campos son obligatorios"}), 400

    actividad = db.session.get(Actividades, activity_id)
    if not actividad:
        return jsonify({"error": "Actividad no encontrada"}), 404

    try:
        fecha_hora = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    except ValueError:
        return jsonify({"error": "Fecha u hora inválida"}), 400

    # 1. Buscamos si ya existe CUALQUIER registro en ese horario para esta actividad
    target_str = fecha_hora.strftime("%Y-%m-%d %H:%M")
    all_activity_classes = Class.query.filter_by(id_actividad=actividad.id).all()
    
    existing_class = None
    for c in all_activity_classes:
        if c.fecha_hora and c.fecha_hora.strftime("%Y-%m-%d %H:%M") == target_str:
            existing_class = c
            break
    
    if existing_class:
        # Si la clase existe y sigue ACTIVA, rebota normalmente
        if getattr(existing_class, "estado", Class.STATUS_ACTIVE) == Class.STATUS_ACTIVE:
            return jsonify({"error": "Ya existe una clase activa para esa actividad en ese horario"}), 400
        
        # 🌟 SI EXISTÍA PERO ESTABA CANCELADA: La reactivamos sin tocar los registros hijos
        existing_class.estado = Class.STATUS_ACTIVE
        existing_class.cupoMaximo = cupo_maximo
        
        try:
            db.session.commit()
            return jsonify({
                "message": "Clase reactivada correctamente en este horario",
                "class": {
                    "id": existing_class.id,
                    "name": existing_class.name,
                    "fecha_hora": existing_class.fecha_hora.isoformat(),
                    "activity_id": existing_class.id_actividad
                }
            }), 201
        except Exception as err:
            db.session.rollback()
            return jsonify({"error": f"Error interno al reactivar la clase: {str(err)}"}), 500

    # 2. Si el horario estaba virgen, creamos un registro nuevo desde cero
    new_class = Class(name=actividad.name, fecha_hora=fecha_hora, id_actividad=actividad.id, cupoMaximo=cupo_maximo)
    db.session.add(new_class)
    
    try:
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
            "activity_id": new_class.id_actividad
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
    cancellation = cancellation_service.cancel_class(class_obj, current_datetime)

    try:
        db.session.commit()
    except Exception as err:
        db.session.rollback()
        logger.exception("[Cancelaciones] error class_id=%s", clase_id)
        return jsonify({"error": "Error interno al procesar la cancelación", "details": str(err)}), 500

    emails_sent = 0
    for user, cancelled_class, credit in cancellation["email_jobs"]:
        if send_class_cancelled_email(user, cancelled_class, credit_generated=credit is not None):
            emails_sent += 1
        if credit and send_credit_generated_email(user, cancelled_class, credit):
            emails_sent += 1

    return jsonify({
        "message": f"Clase '{class_obj.name}' cancelada exitosamente. El turno fue liberado en el calendario.",
        "class_id": clase_id,
        "class_name": class_obj.name,
        "estado": Class.STATUS_CANCELLED,
        "credits_created": cancellation["credits_created"],
        "notifications_created": cancellation["notifications_created"],
        "emails_sent": emails_sent,
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

@app.route("/api/payments/create", methods=["POST"])
def create_payment():
    current_user = _get_authenticated_user()
    if not current_user:
        return jsonify({"error": "No autenticado"}), 401

    data = request.get_json() or {}
    payment_method = data.get("payment_method", Payment.METHOD_MERCADO_PAGO)
    enrollment_id = data.get("enrollment_id")
    requested_payment_type = data.get("payment_type", PAYMENT_TYPE_FULL)

    if payment_method not in Payment.VALID_PAYMENT_METHODS:
        return jsonify({"error": "Método de pago inválido"}), 400

    if requested_payment_type not in Payment.VALID_PAYMENT_TYPES:
        return jsonify({"error": "Tipo de pago inválido"}), 400

    if payment_method != Payment.METHOD_MERCADO_PAGO:
        return jsonify({"error": "Por ahora solo está disponible Mercado Pago Checkout Pro"}), 400

    if not enrollment_id:
        return jsonify({"error": "Debe seleccionar una inscripción pendiente para pagar"}), 400

    enrollment = Enrollment.query.get(enrollment_id)
    current_datetime = _current_discount_datetime()
    error, status_code = _validate_enrollment_payable(enrollment, current_user, current_datetime)
    if error:
        return jsonify({"error": error}), status_code

    class_obj = enrollment.class_
    product_type = _payment_type_for_enrollment(enrollment)

    if product_type == "single_class" or enrollment.tipo == ENROLLMENT_TYPE_SINGLE:
        amount = 3000.0
    else:
        amount = _get_monthly_base_price(class_obj)

    discount_percentage = int(class_obj.descuento or 0)
    full_final_amount = amount - (amount * discount_percentage / 100)
    enrollment.total_amount = float(enrollment.total_amount or 0) or round(full_final_amount, 2)
    payment_service.recompute_enrollment_payment_state(enrollment, current_datetime)
    remaining_amount = float(enrollment.remaining_amount or 0)
    if requested_payment_type == PAYMENT_TYPE_FULL and float(enrollment.paid_amount or 0) > 0:
        requested_payment_type = PAYMENT_TYPE_BALANCE

    if remaining_amount <= 0:
        enrollment.estado = Enrollment.STATUS_PAID
        payment_service.recompute_enrollment_payment_state(enrollment, current_datetime)
        db.session.commit()
        return jsonify({"error": "La inscripción ya está pagada"}), 409

    amount, final_amount = payment_service.payment_amounts_for_type(
        enrollment,
        requested_payment_type,
        amount,
        full_final_amount,
    )

    if final_amount <= 0:
        return jsonify({"error": "No hay saldo pendiente para este tipo de pago"}), 400
    if final_amount > remaining_amount + 0.01:
        return jsonify({"error": "El pago supera el saldo pendiente"}), 400

    _log_discount_quote(current_datetime, class_obj, discount_percentage, amount, final_amount)

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
        "payer": {
            "name": current_user.username,
            "email": current_user.email,
        },
        "external_reference": str(payment.id),
        "back_urls": {
            "success": _configured_url("PAYMENT_SUCCESS_URL", "http://localhost:5000/api/payments/return/success"),
            "failure": _configured_url("PAYMENT_FAILURE_URL", "http://localhost:5000/api/payments/return/failure"),
            "pending": _configured_url("PAYMENT_PENDING_URL", f"http://localhost:5000/api/payments/return/{PAYMENT_RETURN_STATUS_PENDING}"),
        },
        "auto_return": "approved",
    }

    back_urls_error = _validate_mercado_pago_back_urls(preference_data)
    if back_urls_error:
        logger.error("[MercadoPago] back_urls_invalidas error=%s payload=%s", back_urls_error, preference_data)
        db.session.rollback()
        return jsonify({"error": f"Configuración inválida de Mercado Pago: {back_urls_error}"}), 500

    try:
        _log_mercado_pago_payload(preference_data)
        preference_result = get_mercadopago_client().preference().create(preference_data)
        _log_mercado_pago_response(preference_result)
    except RuntimeError as err:
        logger.exception("[MercadoPago] configuracion_invalida")
        db.session.rollback()
        return jsonify({"error": str(err)}), 500
    except Exception as err:
        logger.exception("[MercadoPago] sdk_error")
        db.session.rollback()
        return jsonify({"error": f"Error del SDK de Mercado Pago: {str(err)}"}), 502

    if not isinstance(preference_result, dict):
        logger.error("[MercadoPago] respuesta_invalida response=%s", preference_result)
        db.session.rollback()
        return jsonify({"error": "Mercado Pago devolvió una respuesta inválida"}), 502

    if preference_result.get("status") not in [200, 201]:
        logger.error("[MercadoPago] preferencia_rechazada response=%s", preference_result)
        db.session.rollback()
        response_body = preference_result.get("response") or {}
        mp_message = response_body.get("message") or response_body.get("error") or "Error del servidor de pagos"
        return jsonify({"error": f"Mercado Pago rechazó la preferencia: {mp_message}"}), 502

    preference_response = preference_result.get("response", {})
    if not isinstance(preference_response, dict):
        logger.error("[MercadoPago] body_invalido body=%s response=%s", preference_response, preference_result)
        db.session.rollback()
        return jsonify({"error": "Mercado Pago no devolvió un body válido"}), 502

    init_point = _mercado_pago_checkout_url(preference_response)
    preference_id = preference_response.get("id")
    logger.info(
        "[MercadoPago] preferencia_creada payment_id=%s preference_id=%s checkout_url=%s",
        payment.id,
        preference_id,
        init_point,
    )

    if not init_point:
        logger.error("[MercadoPago] init_point_faltante response=%s", preference_result)
        db.session.rollback()
        return jsonify({"error": "Mercado Pago no devolvió init_point para el checkout"}), 502

    if not preference_id:
        logger.error("[MercadoPago] preference_id_faltante response=%s", preference_result)
        db.session.rollback()
        return jsonify({"error": "Mercado Pago no devolvió id de preferencia"}), 502

    payment.mercado_pago_preference_id = preference_id
    db.session.commit()

    return jsonify({
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

    if payment.status == Payment.STATUS_APPROVED:
        redirect_status = PAYMENT_RETURN_STATUS_SUCCESS
        message = None
    elif (
        payment.enrollment
        and _class_has_finished(payment.enrollment.class_, current_datetime)
    ):
        payment.status = Payment.STATUS_EXPIRED
        if payment.enrollment.estado == Enrollment.STATUS_PENDING_PAYMENT:
            payment.enrollment.estado = Enrollment.STATUS_EXPIRED
        payment_service.recompute_enrollment_payment_state(payment.enrollment, current_datetime)
        redirect_status = PAYMENT_RETURN_STATUS_FAILURE
        message = "El período de pago de la inscripción venció"
    elif result == PAYMENT_RETURN_STATUS_SUCCESS or mercado_pago_status == MERCADO_PAGO_STATUS_APPROVED:
        if _payment_would_overpay(payment):
            payment.status = Payment.STATUS_REJECTED
            redirect_status = PAYMENT_RETURN_STATUS_FAILURE
            message = "El pago supera el saldo pendiente"
        else:
            payment.status = Payment.STATUS_APPROVED
            if payment.enrollment:
                payment_service.recompute_enrollment_payment_state(payment.enrollment, current_datetime)
            redirect_status = PAYMENT_RETURN_STATUS_SUCCESS
            message = None
    elif result == PAYMENT_RETURN_STATUS_PENDING or mercado_pago_status in [
        MERCADO_PAGO_STATUS_PENDING,
        MERCADO_PAGO_STATUS_IN_PROCESS,
    ]:
        payment.status = Payment.STATUS_PENDING
        redirect_status = PAYMENT_RETURN_STATUS_PENDING
        message = None
    else:
        payment.status = Payment.STATUS_REJECTED
        redirect_status = PAYMENT_RETURN_STATUS_FAILURE
        message = _payment_error_message(status_detail)

    db.session.commit()
    logger.info(
        "[MercadoPago Callback] payment_id=%s status=%s redirect_status=%s",
        payment.id,
        payment.status,
        redirect_status,
    )
    return redirect(_frontend_payments_url(redirect_status, message))


@app.route("/api/payments/history", methods=["GET"])
def payment_history():
    current_user = _get_authenticated_user()
    if not current_user:
        return jsonify({"error": "No autenticado"}), 401

    current_datetime = _current_discount_datetime()
    enrollments = Enrollment.query.filter_by(user_id=current_user.id).all()
    changed = False
    for enrollment in enrollments:
        changed = _restore_future_expired_enrollment_if_needed(enrollment, current_datetime) or changed
        changed = _expire_enrollment_if_needed(enrollment, current_datetime) or changed
        changed = payment_service.recompute_enrollment_payment_state(enrollment, current_datetime) or changed

    if changed:
        db.session.commit()

    payments = (
        Payment.query
        .filter_by(user_id=current_user.id)
        .order_by(Payment.created_at.desc())
        .all()
    )

    return jsonify({"payments": [payment.to_dict() for payment in payments]}), 200


@app.route("/api/admin/enrollments/payments", methods=["GET"])
def admin_payment_enrollments():
    current_user = _get_authenticated_user()
    if not current_user:
        return jsonify({"error": "No autenticado"}), 401
    if current_user.role not in ["admin", "employee"]:
        return jsonify({"error": "No tienes permisos para consultar pagos"}), 403

    current_datetime = _current_discount_datetime()
    enrollments = (
        Enrollment.query
        .join(User, Enrollment.user_id == User.id)
        .order_by(Enrollment.id.desc())
        .all()
    )

    payload = []
    changed = False
    for enrollment in enrollments:
        changed = payment_service.recompute_enrollment_payment_state(enrollment, current_datetime) or changed
        if float(enrollment.remaining_amount or 0) <= 0:
            continue
        item = _enrollment_payload(enrollment, current_datetime)
        item["user"] = enrollment.user.to_dict() if enrollment.user else None
        payload.append(item)

    if changed:
        db.session.commit()

    return jsonify({"enrollments": payload}), 200


@app.route("/api/enrollments/<int:enrollment_id>/manual-payment", methods=["POST"])
def register_manual_payment(enrollment_id):
    current_user = _get_authenticated_user()
    if not current_user:
        return jsonify({"error": "No autenticado"}), 401
    if current_user.role not in ["admin", "employee"]:
        return jsonify({"error": "No tienes permisos para registrar pagos"}), 403

    enrollment = Enrollment.query.get(enrollment_id)
    if not enrollment:
        return jsonify({"error": "Inscripción no encontrada"}), 404
    if enrollment.estado in [Enrollment.STATUS_CANCELLED, Enrollment.STATUS_EXPIRED]:
        return jsonify({"error": "No se puede registrar un pago sobre una inscripción cerrada"}), 400

    data = request.get_json() or {}
    payment_method = data.get("payment_method", Payment.METHOD_CASH)
    payment_type = data.get("payment_type", PAYMENT_TYPE_BALANCE)
    notes = data.get("notes")

    if payment_method not in [Payment.METHOD_CASH, Payment.METHOD_TRANSFER, Payment.METHOD_CARD]:
        return jsonify({"error": "Método presencial inválido"}), 400
    if payment_type not in [PAYMENT_TYPE_FULL, PAYMENT_TYPE_BALANCE]:
        return jsonify({"error": "Tipo de pago presencial inválido"}), 400

    try:
        amount = round(float(data.get("amount", 0)), 2)
    except (TypeError, ValueError):
        return jsonify({"error": "El monto debe ser numérico"}), 400

    payment_service.recompute_enrollment_payment_state(enrollment, _current_discount_datetime())
    remaining_amount = round(float(enrollment.remaining_amount or 0), 2)
    if amount <= 0:
        return jsonify({"error": "El monto debe ser mayor a cero"}), 400
    if amount > remaining_amount + 0.01:
        return jsonify({"error": "El pago supera el saldo pendiente"}), 400

    payment = Payment(
        user_id=enrollment.user_id,
        enrollment_id=enrollment.id,
        class_id=enrollment.class_id,
        product_type=_payment_type_for_enrollment(enrollment),
        payment_type=payment_type,
        payment_method=payment_method,
        amount=amount,
        discount_percentage=0,
        final_amount=amount,
        registered_by_user_id=current_user.id,
        notes=notes,
        status=Payment.STATUS_APPROVED,
    )
    db.session.add(payment)
    db.session.flush()
    payment_service.recompute_enrollment_payment_state(enrollment, _current_discount_datetime())
    db.session.commit()

    return jsonify({
        "message": "Pago presencial registrado",
        "payment": payment.to_dict(),
        "enrollment": _enrollment_payload(enrollment, _current_discount_datetime()),
    }), 201


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
