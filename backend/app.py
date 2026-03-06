from flask import Flask, request, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_cors import CORS
from dotenv import load_dotenv
from models import db, User, Note
import os

load_dotenv()

app = Flask(__name__)

# ─── Configuración ────────────────────────────────────────────────────────────
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/demo_db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# CORS: permite que Vue (puerto 5173) le hable al backend (puerto 5000)
CORS(app, supports_credentials=True, origins=["http://localhost:5173"])

# ─── Extensiones ──────────────────────────────────────────────────────────────
db.init_app(app)

login_manager = LoginManager(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Flask-Login por defecto redirige a /login si no autenticado,
# pero como usamos una API JSON, devolvemos 401
@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({"error": "No autenticado"}), 401


# ─── Rutas de Auth ────────────────────────────────────────────────────────────

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()

    if not data or not all(k in data for k in ("username", "email", "password")):
        return jsonify({"error": "Faltan campos requeridos"}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "El email ya está registrado"}), 409

    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "El username ya está en uso"}), 409

    user = User(username=data["username"], email=data["email"])
    user.set_password(data["password"])

    db.session.add(user)
    db.session.commit()

    login_user(user)
    return jsonify({"message": "Usuario creado", "user": user.to_dict()}), 201


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data or not all(k in data for k in ("email", "password")):
        return jsonify({"error": "Faltan campos requeridos"}), 400

    user = User.query.filter_by(email=data["email"]).first()

    if not user or not user.check_password(data["password"]):
        return jsonify({"error": "Email o contraseña incorrectos"}), 401

    login_user(user, remember=data.get("remember", False))
    return jsonify({"message": "Login exitoso", "user": user.to_dict()})


@app.route("/api/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logout exitoso"})


@app.route("/api/me", methods=["GET"])
@login_required
def me():
    return jsonify({"user": current_user.to_dict()})


# ─── Rutas de Notas (CRUD ejemplo) ────────────────────────────────────────────

@app.route("/api/notes", methods=["GET"])
@login_required
def get_notes():
    notes = Note.query.filter_by(user_id=current_user.id).order_by(Note.created_at.desc()).all()
    return jsonify({"notes": [n.to_dict() for n in notes]})


@app.route("/api/notes", methods=["POST"])
@login_required
def create_note():
    data = request.get_json()

    if not data or "title" not in data:
        return jsonify({"error": "El título es requerido"}), 400

    note = Note(
        title=data["title"],
        content=data.get("content", ""),
        user_id=current_user.id,
    )
    db.session.add(note)
    db.session.commit()
    return jsonify({"note": note.to_dict()}), 201


@app.route("/api/notes/<int:note_id>", methods=["DELETE"])
@login_required
def delete_note(note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first_or_404()
    db.session.delete(note)
    db.session.commit()
    return jsonify({"message": "Nota eliminada"})


# ─── Inicialización ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("✅ Tablas creadas / verificadas")
    app.run(debug=True, port=5000)
