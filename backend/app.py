import os
from datetime import datetime, timedelta
from calendar import monthrange
from dotenv import load_dotenv

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from models import db, User
# Importamos todos los modelos requeridos de models.py (incluyendo Credito que mudamos ahí)
from models import Class, Enrollment, Attendance, Actividades, Credito

# Carga variables de entorno desde .env
load_dotenv()

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
    ).group_by(Enrollment.class_id).all():
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
        "estado": getattr(class_obj, "estado", "Activa"),
        "descuento": class_obj.descuento,
    }

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
    for class_obj in Class.query.filter_by(estado="Activa").all():
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
    all_classes = []
    for class_obj in Class.query.all():
        enrolled_count = enrollment_map.get(class_obj.id, 0)
        payload = _class_slot_payload(class_obj, enrolled_count)
        all_classes.append(payload)
    return jsonify({"classes": all_classes}), 200


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

    classes = Class.query.filter_by(id_actividad=actividad_id, estado="Activa").filter(db.func.date(Class.fecha_hora) == day).order_by(Class.fecha_hora).all()

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

    classes = Class.query.filter_by(id_actividad=actividad_id, estado="Activa").filter(Class.fecha_hora >= start, Class.fecha_hora <= end).all()

    for class_obj in classes:
        enrolled_count = enrollment_map.get(class_obj.id, 0)
        cupo_max = class_obj.cupoMaximo if class_obj.cupoMaximo is not None else 20
        if enrolled_count < cupo_max:
            dates_with_cupo.add(class_obj.fecha_hora.date().isoformat())

    return jsonify({"dates": sorted(dates_with_cupo)}), 200

# ─── Rutas API: Gestión de Clases (Compañero) ───────────────────────────

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
    if class_obj.estado == "Cancelada":
        return jsonify({"error": "Esta clase ya fue cancelada"}), 400

    # Marca la clase como cancelada
    class_obj.estado = "Cancelada"

    try:
        db.session.commit()
    except Exception as err:
        db.session.rollback()
        return jsonify({"error": "Error interno al procesar la cancelación", "details": str(err)}), 500

    return jsonify({
        "message": f"Clase '{class_obj.name}' cancelada exitosamente. El turno fue liberado en el calendario.",
        "class_id": clase_id,
        "class_name": class_obj.name,
        "estado": "Cancelada"
    }), 200


# ─── Arranque del Servidor ───────────────────────────────────────────────────

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

    if descuento not in [40, 70]:
        return jsonify({"error": "Porcentaje de descuento no válido"}), 400

    # Lógica acumulativa: si tiene ambos, el valor es 110
    if class_obj.descuento == 110 or class_obj.descuento == descuento:
        return jsonify({"error": "Este descuento ya está aplicado a la clase"}), 400

    if class_obj.descuento in [40, 70]:
        class_obj.descuento = 110
    else:
        class_obj.descuento = descuento

    db.session.commit()

    return jsonify({
        "message": "Descuento aplicado con éxito",
        "class": class_obj.to_dict()
    }), 200

if __name__ == "__main__":
    app.run(debug=True)