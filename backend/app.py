# Este módulo define la aplicación Flask que sirve como API REST para la autenticación de usuarios.
# Configura la conexión a PostgreSQL mediante SQLAlchemy, gestiona sesiones con Flask‑Login y permite
# el registro, inicio de sesión, cierre de sesión y consulta del usuario actual. Además habilita CORS
# para que el frontend Vue (puerto 5173) pueda comunicarse con el backend (puerto 5000). Al ejecutarse
# directamente, crea las tablas en la base de datos y arranca el servidor en modo debug.

from flask import Flask, request, jsonify #Flask crea la aplicación web, request maneja las solicitudes entrantes y jsonify convierte respuestas a JSON
from flask_login import LoginManager, login_user, login_required, logout_user, current_user #simplifica la gestión de sesiones y autenticación de usuarios
from flask_cors import CORS #Permite que el frontend (en otro dominio/puerto) acceda a la API del backend sin problemas de CORS
from dotenv import load_dotenv #Carga variables de entorno desde un archivo .env, útil para configurar cosas como la conexión a la base de datos sin hardcodear credenciales
from models import db, User #Importa la instancia de SQLAlchemy (db) y el modelo de usuario (User) definidos en models.py
import os #Permite acceder a variables de entorno y otras funcionalidades del sistema operativo

load_dotenv()

app = Flask(__name__)

# ─── Configuración ────────────────────────────────────────────────────────────
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key") #firma cookies y protege contra ataques CSRF, en producción debería ser un valor seguro y no hardcodeado
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/demo_db" #URL  de conexión a la base de datos PostgreSQL, se usa demo_db por defecto para desarrollo local, pero en producción debería configurarse con credenciales seguras y posiblemente usar variables de entorno para no exponerlas en el código
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# CORS: permite que Vue (puerto 5173) le hable al backend (puerto 5000)
CORS(app, supports_credentials=True, origins=["http://localhost:5173"])

# ─── Extensiones ──────────────────────────────────────────────────────────────
db.init_app(app)

login_manager = LoginManager(app) # crea una instancia de LoginManager y la asocia con la aplicación Flask, lo que permite gestionar la autenticación de usuarios y las sesiones de manera sencilla

@login_manager.user_loader # decorador que indica a Flask-Login cómo cargar un usuario a partir de su ID almacenado en la sesión, en este caso se consulta la base de datos usando SQLAlchemy para obtener el usuario correspondiente
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
    data = request.get_json() # obtiene los datos enviados en el cuerpo de la solicitud POST como JSON, que deberían incluir username, email y password para registrar un nuevo usuario
    # Validación básica: verifica que se hayan proporcionado los campos requeridos y que el email y username no estén ya registrados en la base de datos. 
    if not data or not all(k in data for k in ("username", "email", "password")):
        return jsonify({"error": "Faltan campos requeridos"}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "El email ya está registrado"}), 409

    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "El username ya está en uso"}), 409

    #Si todo es correcto, crea un nuevo usuario, guarda su contraseña de forma segura (hashing) y lo agrega a la base de datos.
    user = User(username=data["username"], email=data["email"])
    user.set_password(data["password"])

    db.session.add(user)
    db.session.commit()

    #Luego inicia sesión automáticamente al nuevo usuario y devuelve una respuesta JSON con un mensaje de éxito y los datos del usuario registrado.
    login_user(user)
    return jsonify({"message": "Usuario creado", "user": user.to_dict()}), 201


# Igual que el registro, pero en este caso se valida que el email exista y que la contraseña coincida con la almacenada (usando hashing).
# Si es correcto, inicia sesión al usuario y devuelve un mensaje de éxito junto con los datos del usuario.
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

# Cierre de sesión, que requiere que el usuario esté autenticado (gracias a @login_required). Al cerrar sesión, se devuelve un mensaje de éxito.
@app.route("/api/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logout exitoso"})


@app.route("/api/me", methods=["GET"])
@login_required
def me():
    return jsonify({"user": current_user.to_dict()})



# ─── Inicialización ───────────────────────────────────────────────────────────
# Esto es lo que se ejecuta si corremos este archivo directamente (python app.py).
# Crea las tablas en la base de datos (si no existen) y arranca el servidor Flask en modo debug en el puerto 5000.
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("✅ Tablas creadas / verificadas")
    app.run(debug=True, port=5000)
