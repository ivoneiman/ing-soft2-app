from flask_sqlalchemy import SQLAlchemy # SQLAlchemy es un Object-Relational Mapper que traduce objetos Python a tablas SQL y viceversa.
from flask_login import UserMixin # Permite heredar funcionalidades de gestión de usuarios (como autenticación y sesiones) en la clase User.
from werkzeug.security import generate_password_hash, check_password_hash # Ofrece funciones seguras para hash de contraseñas

# Creación del Objeto: se crea la instancia global que será usada por todos los modelos. 
db = SQLAlchemy()

# Definición del Modelo de Usuario
class User(UserMixin, db.Model):
    __tablename__ = "users" 

    id = db.Column(db.Integer, primary_key=True) 
    username = db.Column(db.String(80), unique=True, nullable=False) 
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default="client") # Rol del usuario: client, employee, admin

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
        }

# ---------------------------------------------------------------------------
# Modelos para la funcionalidad de clases, actividades y asistencia QR
# ---------------------------------------------------------------------------

class Actividades(db.Model):
    """Representa las actividades disponibles en el gym."""
    __tablename__ = "actividades"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)


class Class(db.Model):
    """Representa una clase a la que los usuarios pueden inscribirse."""
    __tablename__ = "classes"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    fecha_hora = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False, default=60)
    cupoMaximo = db.Column(db.Integer, nullable=False, default=20)
    id_actividad = db.Column(db.Integer, db.ForeignKey("actividades.id"), nullable=False)

    # Relación con la actividad (necesaria para el catálogo y respuestas limpias)
    actividad = db.relationship("Actividades", backref="classes")

    # Relaciones con inscripciones y asistencias
    enrollments = db.relationship("Enrollment", back_populates="class_", cascade="all, delete-orphan")
    attendances = db.relationship("Attendance", back_populates="class_", cascade="all, delete-orphan")

    # Identificador único unificado para el try/except de app.py de tu compañero
    __table_args__ = (
        db.UniqueConstraint("id_actividad", "fecha_hora", name="actividad_horario_unico"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "fecha_hora": self.fecha_hora.isoformat() if self.fecha_hora else None,
            "duration_minutes": self.duration_minutes,
            "cupoMaximo": self.cupoMaximo,
            "actividad_name": self.actividad.name if self.actividad else None,
        }


class Enrollment(db.Model):
    """Enlace many‑to‑many entre User y Class."""
    __tablename__ = "enrollments"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=False)

    user = db.relationship("User", backref=db.backref("enrollments", cascade="all, delete-orphan"))
    class_ = db.relationship("Class", back_populates="enrollments")

    # Garantizar que un usuario no se inscriba dos veces a la misma clase
    __table_args__ = (db.UniqueConstraint("user_id", "class_id", name="uq_user_class"),)


class Attendance(db.Model):
    """Registro de asistencia de un usuario a una clase."""
    __tablename__ = "attendances"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    user = db.relationship("User", backref=db.backref("attendances", cascade="all, delete-orphan"))
    class_ = db.relationship("Class", back_populates="attendances")

    __table_args__ = (db.UniqueConstraint("user_id", "class_id", name="uq_attendance_user_class"),)