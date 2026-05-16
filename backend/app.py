import os
import re 
from dotenv import load_dotenv

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from models import db, User
# Importar nuevos modelos
from models import Class, Enrollment, Attendance

# Carga variables de entorno desde .env
load_dotenv()

app = Flask(__name__)

# ─── Configuración ────────────────────────────────────────────────────────────

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
app.config["SESSION_COOKIE_SAMESITE"] = "None"
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True

# Base de datos: SQLite por defecto (desarrollo local)
# Configurable desde variable de entorno SQLALCHEMY_DATABASE_URI
# Ejemplos:
#   - SQLite (local):       sqlite:///app.db
#   - PostgreSQL (remoto):  postgresql://user:pass@host:5432/db
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///app.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Inicializa extensiones
db.init_app(app)


def validar_password(password):
    if len(password) < 6:
        return 'La contraseña debe tener al menos 6 caracteres'
    return None

# CORS para frontend local Vue/Vite
CORS(
    app,
    supports_credentials=True,
    origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ]
)

# ─── Revisar esquema de usuarios y crear tablas automáticamente ───────────────

def migrate_remove_username_unique():
    """
    Solo ejecuta la migración si SQLite tiene el constraint UNIQUE(username).
    Esto evita correr la migración innecesariamente en futuras ejecuciones.
    """
    if db.engine.dialect.name != 'sqlite':
        return

    try:
        with db.engine.connect() as conn:
            result = conn.execute(text("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'"))
            row = result.fetchone()
            
            # Si no existe la tabla o no tiene el UNIQUE(username), no hacer nada
            if not row or 'UNIQUE (username)' not in row[0]:
                return
            
            print("[MIGRATE] Removiendo UNIQUE constraint de username...")
            conn.execute(text('PRAGMA foreign_keys=off'))
            conn.execute(text('ALTER TABLE users RENAME TO users_old'))
            conn.execute(text(
                'CREATE TABLE users ('
                'id INTEGER NOT NULL PRIMARY KEY, '
                'username VARCHAR(80) NOT NULL, '
                'apellido VARCHAR(80) NOT NULL, '
                'email VARCHAR(120) NOT NULL UNIQUE, '
                'dni VARCHAR(20) NOT NULL, '
                'telefono VARCHAR(20) NOT NULL, '
                'password_hash VARCHAR(256) NOT NULL, '
                'role VARCHAR(20)'
                ')'
            ))
            conn.execute(text(
                'INSERT INTO users (id, username, apellido, email, dni, telefono, password_hash, role) '
                'SELECT id, username, apellido, email, dni, telefono, password_hash, role FROM users_old'
            ))
            conn.execute(text('DROP TABLE users_old'))
            conn.execute(text('PRAGMA foreign_keys=on'))
            conn.commit()
            print("[MIGRATE] Migration completada")
    except Exception as e:
        print(f"[MIGRATE ERROR] {e}")

with app.app_context():
    migrate_remove_username_unique()
    db.create_all()

# ─── Rutas API ────────────────────────────────────────────────────────────────

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json() or {}

    username  = data.get("username", "").strip()
    apellido  = data.get("apellido", "").strip()
    email     = data.get("email", "").strip()
    dni       = data.get("dni", "").strip()
    telefono  = data.get("telefono", "").strip()
    password  = data.get("password", "")

    if not all([username, apellido, email, dni, telefono, password]):
        return jsonify({"error": "Todos los campos son obligatorios"}), 400

    error_pass = validar_password(password)
    if error_pass:
        return jsonify({"error": error_pass}), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "El email ya está registrado"}), 400

    new_user = User(
        username=username,
        apellido=apellido,
        email=email,
        dni=dni,
        telefono=telefono,
        role="client"
    )
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "Usuario registrado correctamente"}), 201


@app.route("/api/users", methods=["POST"])
def create_user():
    data = request.get_json() or {}

    username  = data.get("username", "").strip()
    apellido  = data.get("apellido", "").strip()
    email     = data.get("email", "").strip()
    dni       = data.get("dni", "").strip()
    telefono  = data.get("telefono", "").strip()
    password  = data.get("password", "")

    if not all([username, apellido, email, dni, telefono, password]):
        return jsonify({"error": "Todos los campos son obligatorios"}), 400

    error_pass = validar_password(password)
    if error_pass:
        return jsonify({"error": error_pass}), 400

    current_user_id = session.get("user_id")
    if not current_user_id:
        return jsonify({"error": "No autenticado"}), 401

    current_user = User.query.get(current_user_id)
    if not current_user or current_user.role not in ["admin", "employee"]:
        return jsonify({"error": "No autorizado"}), 403

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "El email ya está registrado"}), 400

    new_user = User(
        username=username,
        apellido=apellido,
        email=email,
        dni=dni,
        telefono=telefono,
        role="client"
    )
    new_user.set_password(password)

    db.session.add(new_user)
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"error": "Error en la base de datos: email duplicado"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error interno del servidor"}), 500

    return jsonify({"message": "Usuario creado correctamente"}), 201


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