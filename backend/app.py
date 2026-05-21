import os
import json
import traceback
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
from calendar import monthrange
from urllib.parse import quote
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from dotenv import load_dotenv

from flask import Flask, request, jsonify, session, redirect
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from mercadopago_config import get_mercadopago_client
from models import db, User
# Importar todos los modelos requeridos
from models import Class, Enrollment, Attendance, Actividades, Credito, Payment

# Carga variables de entorno desde .env
load_dotenv()

DISCOUNT_PERCENTAGES = (0, 40, 70)
DISCOUNT_PERIODS = (
    {"percentage": 0, "start_day": 1, "end_day": 14},
    {"percentage": 40, "start_day": 15, "end_day": 20},
    {"percentage": 70, "start_day": 21, "end_day": None},
)
ENROLLMENT_REOPENABLE_STATUSES = (Enrollment.STATUS_EXPIRED, Enrollment.STATUS_CANCELLED)

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
    if "classes" in inspector.get_table_names():
        columns = [column["name"] for column in inspector.get_columns("classes")]
        if "fecha_hora" not in columns:
            db.session.execute(text("ALTER TABLE classes ADD COLUMN fecha_hora DATETIME"))
        if "cupoMaximo" not in columns:
            db.session.execute(text("ALTER TABLE classes ADD COLUMN cupoMaximo INTEGER DEFAULT 20"))
        if "id_actividad" not in columns:
            db.session.execute(text("ALTER TABLE classes ADD COLUMN id_actividad INTEGER"))
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

    if "enrollments" in inspector.get_table_names():
        columns = [column["name"] for column in inspector.get_columns("enrollments")]
        if "created_at" not in columns:
            db.session.execute(text("ALTER TABLE enrollments ADD COLUMN created_at DATETIME"))
            db.session.commit()
        db.session.execute(text("UPDATE enrollments SET estado = :new_status WHERE estado = :legacy_status"), {
            "new_status": Enrollment.STATUS_PAID,
            "legacy_status": Class.STATUS_ACTIVE,
        })
        db.session.execute(text("UPDATE enrollments SET estado = :new_status WHERE estado = :legacy_status"), {
            "new_status": Enrollment.STATUS_CANCELLED,
            "legacy_status": Class.STATUS_CANCELLED,
        })
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

def _enrollment_counts():
    counts = {}
    for class_id, enrolled in db.session.query(
        Enrollment.class_id, db.func.count(Enrollment.id)
    ).filter(Enrollment.estado.in_(Enrollment.CAPACITY_STATUSES)).group_by(Enrollment.class_id).all():
        counts[class_id] = enrolled
    return counts


def _class_slot_payload(class_obj, enrolled_count):
    duration = getattr(class_obj, "duration_minutes", 60)
    cupo_max = class_obj.cupoMaximo if class_obj.cupoMaximo is not None else 20
    available = cupo_max - enrolled_count
    return {
        "id": class_obj.id,
        "name": class_obj.name,
        "actividad": class_obj.actividad.name if hasattr(class_obj, "actividad") and class_obj.actividad else None,
        "fecha_hora": class_obj.fecha_hora.isoformat() if class_obj.fecha_hora else None,
        "time": class_obj.fecha_hora.strftime("%H:%M") if class_obj.fecha_hora else "",
        "duration_minutes": duration,
        "cupoMaximo": cupo_max,
        "enrolled": enrolled_count,
        "available_spots": available,
        "is_full": available <= 0,
        "estado": getattr(class_obj, "estado", Class.STATUS_ACTIVE),
        "descuento": class_obj.descuento,
    }


def _get_authenticated_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)


def _configured_amount(name, default):
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return float(default)


def _app_timezone():
    timezone_name = os.getenv("APP_TIMEZONE", "America/Argentina/Buenos_Aires")
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        print(f"[Discount] timezone inválida: {timezone_name}. Usando hora local del servidor.", flush=True)
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

    print("[Discount Test Mode]", flush=True)
    print(f"real_day={real_datetime.day}", flush=True)
    print(f"effective_day={effective_datetime.day}", flush=True)
    print(f"test_mode={str(test_mode).lower()}", flush=True)

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
    current_datetime = current_datetime or _current_discount_datetime()
    today = current_datetime.day
    last_day = monthrange(current_datetime.year, current_datetime.month)[1]

    for period in DISCOUNT_PERIODS:
        end_day = period["end_day"] or last_day
        if period["start_day"] <= today <= end_day:
            return period["percentage"]

    return 0


def _payment_discount_percentage(current_datetime=None):
    return _current_discount_period_percentage(current_datetime)


def _discount_rules_payload(current_datetime=None):
    current_datetime = current_datetime or _current_discount_datetime()
    last_day = monthrange(current_datetime.year, current_datetime.month)[1]
    return {
        "current_percentage": _payment_discount_percentage(current_datetime),
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


def _class_has_finished(class_obj, current_datetime=None):
    class_datetime = _datetime_in_app_timezone(class_obj.fecha_hora if class_obj else None)
    if not class_datetime:
        return False

    current_datetime = current_datetime or _current_discount_datetime()
    current_datetime = _datetime_in_app_timezone(current_datetime)
    return class_datetime <= current_datetime


def _payment_amount(payment_type, payment_option):
    if payment_type == "monthly_subscription":
        return _configured_amount("PAYMENT_MONTHLY_AMOUNT", 10000)

    amount = _configured_amount("PAYMENT_CLASS_AMOUNT", 3000)
    if payment_option == "deposit":
        deposit_percentage = _configured_amount("PAYMENT_DEPOSIT_PERCENTAGE", 50)
        return amount * (deposit_percentage / 100)
    return amount


def _calculate_final_amount(amount, discount_percentage):
    original_amount = Decimal(str(amount))
    discount = Decimal(str(discount_percentage))
    final_amount = original_amount - (original_amount * discount / Decimal("100"))
    return float(final_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _payment_quote(payment_type, payment_option, current_datetime=None):
    amount = _payment_amount(payment_type, payment_option)
    discount_percentage = _payment_discount_percentage(current_datetime)
    final_amount = _calculate_final_amount(amount, discount_percentage)

    return {
        "amount": amount,
        "discount_percentage": discount_percentage,
        "final_amount": final_amount,
    }


def _payment_type_for_enrollment(enrollment):
    return "monthly_subscription" if getattr(enrollment, "tipo", None) == "Mensual" else "individual_class"


def _expire_enrollment_if_needed(enrollment, current_datetime=None):
    if not enrollment or enrollment.estado != Enrollment.STATUS_PENDING_PAYMENT:
        return False

    if _class_has_finished(enrollment.class_, current_datetime):
        enrollment.estado = Enrollment.STATUS_EXPIRED
        return True

    return False


def _has_approved_payment(enrollment):
    return any(payment.status == Payment.STATUS_APPROVED for payment in getattr(enrollment, "payments", []))


def _class_capacity(class_obj):
    return class_obj.cupoMaximo if class_obj and class_obj.cupoMaximo is not None else 20


def _validate_class_available_for_enrollment(class_obj, current_datetime):
    if not class_obj:
        return "Clase no encontrada", 404
    if getattr(class_obj, "estado", Class.STATUS_ACTIVE) != Class.STATUS_ACTIVE:
        return "La clase no está disponible para inscripción", 400
    if _class_has_finished(class_obj, current_datetime):
        return "No se puede inscribir a una clase que ya comenzó", 400
    return None, None


def _validate_enrollment_payable(enrollment, current_user, current_datetime):
    if not enrollment or enrollment.user_id != current_user.id:
        return "Inscripción no encontrada", 404

    class_obj = enrollment.class_
    if not class_obj:
        return "Clase no encontrada", 404
    if _class_has_finished(class_obj, current_datetime):
        if enrollment.estado == Enrollment.STATUS_PENDING_PAYMENT:
            enrollment.estado = Enrollment.STATUS_EXPIRED
            db.session.commit()
        return "No se puede pagar una clase ya finalizada", 400
    if enrollment.estado != Enrollment.STATUS_PENDING_PAYMENT:
        return "La inscripción no está pendiente de pago", 400
    if _has_approved_payment(enrollment):
        enrollment.estado = Enrollment.STATUS_PAID
        db.session.commit()
        return "La inscripción ya tiene un pago aprobado", 409

    return None, None


def _enrollment_has_other_approved_payment(payment):
    if not payment or not payment.enrollment_id:
        return False

    return (
        Payment.query
        .filter(
            Payment.enrollment_id == payment.enrollment_id,
            Payment.id != payment.id,
            Payment.status == Payment.STATUS_APPROVED,
        )
        .first()
        is not None
    )


def _enrollment_payment_quote(enrollment, current_datetime=None):
    return _payment_quote(_payment_type_for_enrollment(enrollment), "full", current_datetime)


def _enrollment_payload(enrollment, current_datetime=None):
    class_obj = enrollment.class_
    quote = _enrollment_payment_quote(enrollment, current_datetime)
    return {
        "id": enrollment.id,
        "user_id": enrollment.user_id,
        "class_id": enrollment.class_id,
        "class_name": class_obj.name if class_obj else None,
        "actividad": class_obj.actividad.name if class_obj and class_obj.actividad else None,
        "fecha_hora": class_obj.fecha_hora.isoformat() if class_obj and class_obj.fecha_hora else None,
        "estado": enrollment.estado,
        "tipo": enrollment.tipo,
        "expires_at": class_obj.fecha_hora.isoformat() if class_obj and class_obj.fecha_hora else None,
        "payment_type": _payment_type_for_enrollment(enrollment),
        "payment_option": "full",
        "amount": quote["amount"],
        "discount_percentage": quote["discount_percentage"],
        "final_amount": quote["final_amount"],
        "is_payable": enrollment.estado == Enrollment.STATUS_PENDING_PAYMENT and not _class_has_finished(class_obj, current_datetime),
    }


def _log_discount_quote(current_datetime, class_obj, discount_percentage, amount, final_amount):
    class_datetime = _datetime_in_app_timezone(class_obj.fecha_hora if class_obj else None)
    print("[Discount]", flush=True)
    print(f"today={current_datetime.date().isoformat()}", flush=True)
    print(f"class_datetime={class_datetime.isoformat() if class_datetime else None}", flush=True)
    print(f"discount={discount_percentage}", flush=True)
    print(f"original_amount={amount}", flush=True)
    print(f"final_amount={final_amount}", flush=True)


def _payment_error_message(status_detail):
    if status_detail == "cc_rejected_insufficient_amount":
        return "Fondos insuficientes"
    if status_detail and status_detail.startswith("cc_rejected"):
        return "Pago rechazado"
    return "Error del servidor de pagos"


def _frontend_payments_url(status, message=None):
    url = f"{os.getenv('FRONTEND_PAYMENTS_URL', 'http://localhost:5173/pagos')}?status={status}"
    if message:
        url = f"{url}&message={quote(message)}"
    return url


def _configured_url(name, default):
    value = os.getenv(name)
    if value and value.strip():
        return value.strip()
    return default


def _is_absolute_http_url(value):
    return isinstance(value, str) and value.strip().startswith(("http://", "https://"))


def _validate_mercado_pago_back_urls(preference_data):
    if "back_url" in preference_data:
        print("ERROR: back_url singular no debe existir en preference_data", flush=True)
        return "back_urls debe llamarse en plural"

    if "back_urls" not in preference_data:
        print("ERROR: back_urls no existe en preference_data", flush=True)
        return "back_urls debe estar definido como objeto"

    back_urls = preference_data.get("back_urls")
    if not isinstance(back_urls, dict):
        return "back_urls debe estar definido como objeto"

    if "auto_return" in back_urls:
        print("ERROR: auto_return está dentro de back_urls", flush=True)
        return "auto_return debe estar al mismo nivel que back_urls"

    for key in ["success", "failure", "pending"]:
        if key not in back_urls:
            print(f"ERROR: back_urls.{key} no existe en preference_data", flush=True)
            return f"back_urls.{key} debe estar definido"

        value = back_urls.get(key)
        if not value:
            return f"back_urls.{key} debe estar definido"
        if not isinstance(value, str):
            return f"back_urls.{key} debe ser un string"
        if not value.strip():
            return f"back_urls.{key} no puede estar vacío"
        if not _is_absolute_http_url(value):
            return f"back_urls.{key} debe ser una URL absoluta http:// o https://"

    if preference_data.get("auto_return") == "approved" and not _is_absolute_http_url(back_urls.get("success")):
        return "auto_return approved requiere back_urls.success válido"

    if "auto_return" not in preference_data:
        print("ERROR: auto_return no existe en preference_data", flush=True)
        return "auto_return debe estar definido como approved"

    if preference_data.get("auto_return") != "approved":
        return "auto_return debe estar definido como approved"

    return None


def _log_mercado_pago_payload(preference_data):
    print("PAYLOAD FINAL REAL:", flush=True)
    print(json.dumps(preference_data, indent=2, ensure_ascii=False), flush=True)


def _log_mercado_pago_response(preference_result):
    print("[MercadoPago] RESPONSE COMPLETA:", preference_result, flush=True)
    if isinstance(preference_result, dict):
        print("[MercadoPago] STATUS:", preference_result.get("status"), flush=True)
        print("[MercadoPago] BODY:", preference_result.get("response"), flush=True)


def _mercado_pago_checkout_url(preference_response):
    checkout_mode = os.getenv("MERCADOPAGO_CHECKOUT_MODE", os.getenv("ENVIRONMENT", "")).lower()
    if checkout_mode in ["sandbox", "development", "dev"]:
        return preference_response.get("sandbox_init_point") or preference_response.get("init_point")
    return preference_response.get("init_point") or preference_response.get("sandbox_init_point")

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

    if not all([username, apellido, email, dni, telefono, password]):
        return jsonify({"error": "Todos los campos son obligatorios"}), 400

    if len(password) < 6:
        return jsonify({"error": "La contraseña debe tener al menos 6 caracteres"}), 400

    existing_email = User.query.filter_by(email=email).first()
    if existing_email:
        return jsonify({"error": "El email ya está registrado"}), 400

    new_user = User(username=username, apellido=apellido, email=email, dni=dni, telefono=telefono, role="client")
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "Usuario creado exitosamente", "user": new_user.to_dict()}), 201


@app.route("/api/actividades/<int:actividad_id>/classes", methods=["GET"])
def get_activity_classes(actividad_id):
    classes = Class.query.filter_by(id_actividad=actividad_id).all()
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
    """Devuelve TODAS las clases (activas y canceladas) con conteo de inscritos.
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

    classes = Class.query.filter_by(id_actividad=actividad_id, estado=Class.STATUS_ACTIVE).filter(db.func.date(Class.fecha_hora) == day).order_by(Class.fecha_hora).all()

    for class_obj in classes:
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

    classes = Class.query.filter_by(id_actividad=actividad_id, estado=Class.STATUS_ACTIVE).filter(Class.fecha_hora >= start, Class.fecha_hora <= end).all()

    for class_obj in classes:
        enrolled_count = enrollment_map.get(class_obj.id, 0)
        cupo_max = class_obj.cupoMaximo if class_obj.cupoMaximo is not None else 20
        if enrolled_count < cupo_max:
            dates_with_cupo.add(class_obj.fecha_hora.date().isoformat())

    return jsonify({"dates": sorted(dates_with_cupo)}), 200

# ─── Rutas API: Gestión de Clases (Compañero) ───────────────────────────

@app.route("/api/enrollments", methods=["POST"])
def create_enrollment():
    current_user = _get_authenticated_user()
    if not current_user:
        return jsonify({"error": "No autenticado"}), 401

    data = request.get_json() or {}
    class_id = data.get("class_id")
    if not class_id:
        return jsonify({"error": "Debe seleccionar una clase para inscribirse"}), 400

    current_datetime = _current_discount_datetime()
    class_obj = Class.query.get(class_id)
    error, status_code = _validate_class_available_for_enrollment(class_obj, current_datetime)
    if error:
        return jsonify({"error": error}), status_code

    enrollment = Enrollment.query.filter_by(user_id=current_user.id, class_id=class_obj.id).first()
    enrollment_map = _enrollment_counts()
    cupo_max = _class_capacity(class_obj)
    if enrollment:
        _expire_enrollment_if_needed(enrollment, current_datetime)
        if enrollment.estado == Enrollment.STATUS_PAID or _has_approved_payment(enrollment):
            enrollment.estado = Enrollment.STATUS_PAID
            db.session.commit()
            return jsonify({"error": "Ya estás inscripto y pagaste esta clase"}), 409
        if enrollment.estado == Enrollment.STATUS_PENDING_PAYMENT:
            db.session.commit()
            return jsonify({
                "message": "Ya tenés una inscripción pendiente de pago",
                "enrollment": _enrollment_payload(enrollment, current_datetime),
                "payment_url": f"/pagos?tab=pending&enrollment_id={enrollment.id}",
            }), 200
        if enrollment.estado in ENROLLMENT_REOPENABLE_STATUSES:
            if enrollment_map.get(class_obj.id, 0) >= cupo_max:
                db.session.commit()
                return jsonify({"error": "No quedan cupos disponibles para esta clase"}), 409
            enrollment.estado = Enrollment.STATUS_PENDING_PAYMENT
            enrollment.requiere_reembolso = False
    else:
        if enrollment_map.get(class_obj.id, 0) >= cupo_max:
            return jsonify({"error": "No quedan cupos disponibles para esta clase"}), 409
        enrollment = Enrollment(
            user_id=current_user.id,
            class_id=class_obj.id,
            tipo=data.get("tipo") or "Suelta",
            estado=Enrollment.STATUS_PENDING_PAYMENT,
        )
        db.session.add(enrollment)

    db.session.commit()
    return jsonify({
        "message": "Inscripción creada. Podés completar el pago ahora o más adelante.",
        "enrollment": _enrollment_payload(enrollment, current_datetime),
        "payment_url": f"/pagos?tab=pending&enrollment_id={enrollment.id}",
    }), 201


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
        if enrollment.estado == Enrollment.STATUS_PENDING_PAYMENT and not _has_approved_payment(enrollment):
            pending.append(_enrollment_payload(enrollment, current_datetime))

    if changed:
        db.session.commit()

    return jsonify({"enrollments": pending}), 200


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

    actividad = Actividades.query.get(activity_id)
    if not actividad:
        return jsonify({"error": "Actividad no encontrada"}), 404

    try:
        fecha_hora = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    except ValueError:
        return jsonify({"error": "Fecha u hora inválida"}), 400

    existing_class = Class.query.filter_by(id_actividad=actividad.id, fecha_hora=fecha_hora).first()
    if existing_class:
        return jsonify({"error": "Ya existe una clase para esa actividad en ese horario"}), 400

    new_class = Class(name=actividad.name, fecha_hora=fecha_hora, id_actividad=actividad.id, cupoMaximo=cupo_maximo)
    db.session.add(new_class)
    try:
        db.session.commit()
    except IntegrityError as err:
        db.session.rollback()
        error_text = str(err.orig).lower()
        if "actividad_horario_unico" in error_text or "unique constraint" in error_text:
            return jsonify({"error": "Ya existe una clase para esa actividad en ese horario"}), 400
        return jsonify({"error": "Error interno al crear la clase"}), 500

    return jsonify({
        "message": "Clase creada correctamente",
        "class": {"id": new_class.id, "name": new_class.name, "fecha_hora": new_class.fecha_hora.isoformat(), "activity_id": new_class.id_actividad}
    }), 201

# ─── Rutas API: Asistencia QR (ORIGINAL DE TU COMPAÑERO, SIN MODIFICAR) ───────

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
        return jsonify({"error": "Usuario inexistente"}), 404

    class_obj = Class.query.get(class_id)
    if not class_obj:
        return jsonify({"error": "Clase inexistente"}), 404

    enrollment = Enrollment.query.filter_by(user_id=user_id, class_id=class_id).first()
    if not enrollment:
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

# ─── Rutas API: Gestión de Cancelaciones por Staff (US #19) ───────────────────

@app.route("/api/classes/<int:clase_id>/cancelar", methods=["POST"])
def cancelar_clase_staff(clase_id):
    """US #19: El profesor o administrador cancela una clase completa.
    Simplemente marca la clase como cancelada y libera el turno.
    """
    user_id_sesion = session.get("user_id")
    if not user_id_sesion:
        return jsonify({"error": "No autenticado"}), 401

    current_user = User.query.get(user_id_sesion)
    if not current_user or current_user.role not in ["admin", "employee"]:
        return jsonify({"error": "No tienes permisos de personal para cancelar clases"}), 403

    class_obj = Class.query.get_or_404(clase_id)
    
    # Verifica si la clase ya fue cancelada
    if class_obj.estado == Class.STATUS_CANCELLED:
        return jsonify({"error": "Esta clase ya fue cancelada"}), 400

    # Marca la clase como cancelada
    class_obj.estado = Class.STATUS_CANCELLED

    try:
        db.session.commit()
    except Exception as err:
        db.session.rollback()
        return jsonify({"error": "Error interno al procesar la cancelación", "details": str(err)}), 500

    return jsonify({
        "message": f"Clase '{class_obj.name}' cancelada exitosamente. El turno fue liberado en el calendario.",
        "class_id": clase_id,
        "class_name": class_obj.name,
        "estado": Class.STATUS_CANCELLED
    }), 200


# ─── Arranque del Servidor ───────────────────────────────────────────────────

# ─── Rutas API: Pagos ────────────────────────────────────────────────────────

@app.route("/api/payments/create", methods=["POST"])
def create_payment():
    current_user = _get_authenticated_user()
    if not current_user:
        return jsonify({"error": "No autenticado"}), 401

    data = request.get_json() or {}
    payment_method = data.get("payment_method", Payment.METHOD_MERCADO_PAGO)
    enrollment_id = data.get("enrollment_id")
    payment_option = "full"

    if payment_method not in Payment.VALID_PAYMENT_METHODS:
        return jsonify({"error": "Método de pago inválido"}), 400

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
    payment_type = _payment_type_for_enrollment(enrollment)
    quote = _payment_quote(payment_type, payment_option, current_datetime)
    amount = quote["amount"]
    discount_percentage = quote["discount_percentage"]
    final_amount = quote["final_amount"]
    _log_discount_quote(current_datetime, class_obj, discount_percentage, amount, final_amount)

    payment = Payment(
        user_id=current_user.id,
        enrollment_id=enrollment.id,
        payment_type=payment_type,
        payment_method=payment_method,
        amount=amount,
        discount_percentage=discount_percentage,
        final_amount=final_amount,
        status=Payment.STATUS_PENDING,
    )
    db.session.add(payment)
    db.session.flush()

    activity_name = class_obj.actividad.name if class_obj.actividad else class_obj.name
    title = f"Suscripción mensual - {activity_name}" if payment_type == "monthly_subscription" else f"Clase individual - {activity_name}"
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
            "pending": _configured_url("PAYMENT_PENDING_URL", "http://localhost:5000/api/payments/return/pending"),
        },
        "auto_return": "approved",
    }

    back_urls_error = _validate_mercado_pago_back_urls(preference_data)
    if back_urls_error:
        print("[MercadoPago] ERROR BACK_URLS:", back_urls_error, flush=True)
        print("[MercadoPago] PAYLOAD RECHAZADO LOCALMENTE:", flush=True)
        print(json.dumps(preference_data, indent=2, ensure_ascii=False), flush=True)
        db.session.rollback()
        return jsonify({"error": f"Configuración inválida de Mercado Pago: {back_urls_error}"}), 500

    try:
        _log_mercado_pago_payload(preference_data)
        preference_result = get_mercadopago_client().preference().create(preference_data)
        _log_mercado_pago_response(preference_result)
    except RuntimeError as err:
        print("[MercadoPago] ERROR DE CONFIGURACION:", str(err), flush=True)
        traceback.print_exc()
        db.session.rollback()
        return jsonify({"error": str(err)}), 500
    except Exception as err:
        print("[MercadoPago] ERROR MERCADO PAGO:", str(err), flush=True)
        traceback.print_exc()
        db.session.rollback()
        return jsonify({"error": f"Error del SDK de Mercado Pago: {str(err)}"}), 502

    if not isinstance(preference_result, dict):
        print("[MercadoPago] RESPUESTA INVALIDA DEL SDK:", preference_result, flush=True)
        db.session.rollback()
        return jsonify({"error": "Mercado Pago devolvió una respuesta inválida"}), 502

    if preference_result.get("status") not in [200, 201]:
        print("[MercadoPago] ERROR EN CREACION DE PREFERENCIA:", preference_result, flush=True)
        db.session.rollback()
        response_body = preference_result.get("response") or {}
        mp_message = response_body.get("message") or response_body.get("error") or "Error del servidor de pagos"
        return jsonify({"error": f"Mercado Pago rechazó la preferencia: {mp_message}"}), 502

    preference_response = preference_result.get("response", {})
    if not isinstance(preference_response, dict):
        print("[MercadoPago] BODY INVALIDO:", preference_response, flush=True)
        print("[MercadoPago] RESPONSE COMPLETA SIN BODY VALIDO:", preference_result, flush=True)
        db.session.rollback()
        return jsonify({"error": "Mercado Pago no devolvió un body válido"}), 502

    init_point = _mercado_pago_checkout_url(preference_response)
    preference_id = preference_response.get("id")
    print("[MercadoPago] INIT_POINT:", preference_response.get("init_point"), flush=True)
    print("[MercadoPago] SANDBOX_INIT_POINT:", preference_response.get("sandbox_init_point"), flush=True)
    print("[MercadoPago] CHECKOUT_URL_SELECCIONADA:", init_point, flush=True)
    print("[MercadoPago] PREFERENCE_ID:", preference_id, flush=True)

    if not init_point:
        print("[MercadoPago] INIT_POINT FALTANTE O VACIO:", preference_result, flush=True)
        db.session.rollback()
        return jsonify({"error": "Mercado Pago no devolvió init_point para el checkout"}), 502

    if not preference_id:
        print("[MercadoPago] PREFERENCE_ID FALTANTE O VACIO:", preference_result, flush=True)
        db.session.rollback()
        return jsonify({"error": "Mercado Pago no devolvió id de preferencia"}), 502

    payment.mercado_pago_preference_id = preference_id
    db.session.commit()

    return jsonify({
        "payment_id": payment.id,
        "enrollment_id": enrollment.id,
        "init_point": init_point,
        "amount": amount,
        "discount_percentage": discount_percentage,
        "final_amount": final_amount,
    }), 201


@app.route("/api/payments/return/<result>", methods=["GET"])
def mercado_pago_return(result):
    print("[MercadoPago Callback] RESULT:", result, flush=True)
    print("[MercadoPago Callback] QUERY PARAMS:", request.args.to_dict(), flush=True)
    payment_reference = request.args.get("external_reference")
    preference_id = request.args.get("preference_id")
    mercado_pago_payment_id = request.args.get("payment_id") or request.args.get("collection_id")
    mercado_pago_status = request.args.get("status") or request.args.get("collection_status")
    status_detail = request.args.get("status_detail")
    print("[MercadoPago Callback] EXTERNAL_REFERENCE:", payment_reference, flush=True)
    print("[MercadoPago Callback] PREFERENCE_ID:", preference_id, flush=True)
    print("[MercadoPago Callback] PAYMENT_ID:", mercado_pago_payment_id, flush=True)
    print("[MercadoPago Callback] STATUS:", mercado_pago_status, flush=True)
    print("[MercadoPago Callback] STATUS_DETAIL:", status_detail, flush=True)

    payment = None
    if payment_reference:
        payment = Payment.query.get(payment_reference)
    if not payment and preference_id:
        payment = Payment.query.filter_by(mercado_pago_preference_id=preference_id).first()

    if not payment:
        print("[MercadoPago Callback] PAYMENT NO ENCONTRADO", flush=True)
        return redirect(_frontend_payments_url("failure", "Error del servidor de pagos"))

    if mercado_pago_payment_id:
        payment.mercado_pago_payment_id = str(mercado_pago_payment_id)

    if (result == "success" or mercado_pago_status == "approved") and _enrollment_has_other_approved_payment(payment):
        payment.status = Payment.STATUS_REJECTED
        redirect_status = "failure"
        message = "La inscripción ya tiene un pago aprobado"
    elif result == "success" or mercado_pago_status == "approved":
        payment.status = Payment.STATUS_APPROVED
        if payment.enrollment:
            payment.enrollment.estado = Enrollment.STATUS_PAID
        redirect_status = "success"
        message = None
    elif result == "pending" or mercado_pago_status in ["pending", "in_process"]:
        payment.status = Payment.STATUS_PENDING
        redirect_status = "pending"
        message = None
    else:
        payment.status = Payment.STATUS_REJECTED
        redirect_status = "failure"
        message = _payment_error_message(status_detail)

    db.session.commit()
    print("[MercadoPago Callback] PAYMENT DB ID:", payment.id, flush=True)
    print("[MercadoPago Callback] PAYMENT STATUS ACTUALIZADO:", payment.status, flush=True)
    print("[MercadoPago Callback] REDIRECT FRONTEND STATUS:", redirect_status, flush=True)
    return redirect(_frontend_payments_url(redirect_status, message))


@app.route("/api/payments/history", methods=["GET"])
def payment_history():
    current_user = _get_authenticated_user()
    if not current_user:
        return jsonify({"error": "No autenticado"}), 401

    payments = (
        Payment.query
        .filter_by(user_id=current_user.id)
        .order_by(Payment.created_at.desc())
        .all()
    )

    return jsonify({"payments": [payment.to_dict() for payment in payments]}), 200


@app.route("/api/payments/discount-rules", methods=["GET"])
def payment_discount_rules():
    current_datetime = _discount_datetime_from_request()
    return jsonify(_discount_rules_payload(current_datetime)), 200


# ─── Rutas API: Descuentos y Promociones ──────────────────────────────────────

@app.route("/api/classes/<int:class_id>/discount", methods=["PUT"])
def apply_discount(class_id):
    """Permite al administrador aplicar un descuento a una clase validando el día del mes."""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "No autenticado"}), 401

    current_user = User.query.get(user_id)
    if not current_user or current_user.role != "admin":
        return jsonify({"error": "No tienes permisos para realizar esta acción"}), 403

    data = request.get_json() or {}
    descuento = data.get("descuento")

    if descuento is None:
        return jsonify({"error": "Debe especificar un porcentaje de descuento"}), 400

    try:
        descuento = int(descuento)
    except ValueError:
        return jsonify({"error": "El descuento debe ser un número entero"}), 400

    class_obj = Class.query.get(class_id)
    if not class_obj:
        return jsonify({"error": "Clase no encontrada"}), 404

    if descuento not in DISCOUNT_PERCENTAGES:
        return jsonify({"error": "Porcentaje de descuento no válido"}), 400

    if class_obj.descuento == descuento:
        return jsonify({"error": "Este descuento ya está aplicado a la clase"}), 400

    class_obj.descuento = descuento

    db.session.commit()

    return jsonify({
        "message": "Descuento aplicado con éxito",
        "class": class_obj.to_dict()
    }), 200

if __name__ == "__main__":
    app.run(debug=True)
