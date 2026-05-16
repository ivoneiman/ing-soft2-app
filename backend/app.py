import os
from dotenv import load_dotenv
from datetime import datetime

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from models import db, User
# Importar nuevos modelos
from models import Class, Enrollment, Attendance, Actividades

# Carga variables de entorno desde .env
load_dotenv()

app = Flask(__name__)

# ─── Configuración ────────────────────────────────────────────────────────────

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")

# Base de datos: SQLite por defecto (desarrollo local)
# Configurable desde variable de entorno SQLALCHEMY_DATABASE_URI
# Ejemplos:
#   - SQLite (local):       sqlite:///app.db
#   - PostgreSQL (remoto):  postgresql://user:pass@host:5432/db
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///app.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Inicializa extensiones
db.init_app(app)

# CORS para frontend local Vue/Vite
CORS(
    app,
    supports_credentials=True,
    origins=[
        "http://localhost:5173"
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
        db.session.commit()

# ─── Crear tablas automáticamente ─────────────────────────────────────────────────────────────

with app.app_context():
    db.create_all()
    upgrade_database_schema()

# ─── Rutas API ────────────────────────────────────────────────────────────────

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    # Validaciones básicas
    if not username or not email or not password:
        return jsonify({"error": "Todos los campos son obligatorios"}), 400

    # Verificar si ya existe el email
    existing_user = User.query.filter_by(email=email).first()

    if existing_user:
        return jsonify({"error": "El email ya está registrado"}), 400

    # Crear usuario
    hashed_password = generate_password_hash(password)

    new_user = User(
        username=username,
        email=email
    )

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

    # Guardar sesión
    session["user_id"] = user.id

    return jsonify({
        "message": "Login exitoso",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
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
            "email": user.email,
            "role": user.role
        }
    }), 200


@app.route("/api/actividades", methods=["GET"])
def get_actividades():
    actividades = Actividades.query.all()
    return jsonify([
        {"id": actividad.id, "name": actividad.name}
        for actividad in actividades
    ]), 200


@app.route("/api/classes", methods=["POST"])
def create_class():
    data = request.get_json() or {}
    activity_id = data.get("activity_id")
    date = data.get("date")
    time = data.get("time")

    if not activity_id or not date or not time:
        return jsonify({"error": "Todos los campos son obligatorios"}), 400

    actividad = Actividades.query.get(activity_id)
    if not actividad:
        return jsonify({"error": "Actividad no encontrada"}), 404

    try:
        fecha_hora = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    except ValueError:
        return jsonify({"error": "Fecha u hora inválida"}), 400

    existing_class = Class.query.filter_by(
        id_actividad=actividad.id,
        fecha_hora=fecha_hora,
    ).first()

    if existing_class:
        return jsonify({"error": "Ya existe una clase para esa actividad en ese horario"}), 400

    new_class = Class(
        name=actividad.name,
        fecha_hora=fecha_hora,
        id_actividad=actividad.id,
    )

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
        "class": {
            "id": new_class.id,
            "name": new_class.name,
            "fecha_hora": new_class.fecha_hora.isoformat(),
            "activity_id": new_class.id_actividad,
        }
    }), 201


# ---------------------------------------------------------------------------
# Endpoint para registrar asistencia mediante QR
# ---------------------------------------------------------------------------

@app.route("/api/attendance/register", methods=["POST"])
def register_attendance():
    """Registra la asistencia de un usuario a una clase.
    Se espera un JSON con ``user_id`` y ``class_id``.
    Validaciones:
    * El usuario debe existir.
    * La clase debe existir.
    * El usuario debe estar inscrito a la clase (Enrollment).
    * No debe existir una asistencia previa para esa combinación.
    """
    data = request.get_json() or {}
    user_id = data.get("user_id")
    class_id = data.get("class_id")

    # Validación básica de presencia
    if not user_id or not class_id:
        return jsonify({"error": "user_id y class_id son requeridos"}), 400

    # Verificar existencia de usuario y clase
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuario inexistente"}), 404

    class_obj = Class.query.get(class_id)
    if not class_obj:
        return jsonify({"error": "Clase inexistente"}), 404

    # Verificar inscripción
    enrollment = Enrollment.query.filter_by(user_id=user_id, class_id=class_id).first()
    if not enrollment:
        return jsonify({"error": "Usuario no está inscrito a la clase"}), 403

    # Evitar duplicados de asistencia
    existing = Attendance.query.filter_by(user_id=user_id, class_id=class_id).first()
    if existing:
        return jsonify({"error": "Asistencia ya registrada"}), 409

    # Registrar asistencia
    new_attendance = Attendance(user_id=user_id, class_id=class_id)
    db.session.add(new_attendance)
    db.session.commit()

    return jsonify({"message": "Asistencia registrada correctamente", "attendance": {
        "id": new_attendance.id,
        "user_id": new_attendance.user_id,
        "class_id": new_attendance.class_id,
        "created_at": new_attendance.created_at.isoformat()
    }}), 201


if __name__ == "__main__":
    app.run(debug=True)