import os
from dotenv import load_dotenv

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User
# Importar nuevos modelos
from models import Class, Enrollment, Attendance

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

# ─── Crear tablas automáticamente ─────────────────────────────────────────────

with app.app_context():
    db.create_all()

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


# ─── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True)

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