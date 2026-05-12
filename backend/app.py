import os
from dotenv import load_dotenv

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User

# Carga variables de entorno desde .env
load_dotenv()

app = Flask(__name__)

# ─── Configuración ────────────────────────────────────────────────────────────

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")

# Base de datos LOCAL SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
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
            "email": user.email
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
            "email": user.email
        }
    }), 200


# ─── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True)