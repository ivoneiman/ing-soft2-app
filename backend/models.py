from flask_sqlalchemy import SQLAlchemy # SQLAlchemy es un Object-Relational Mapper que traduce objetos Python a tablas SQL y viceversa.
from flask_login import UserMixin # Permite heredar funcionalidades de gestión de usuarios (como autenticación y sesiones) en la clase User.
from werkzeug.security import generate_password_hash, check_password_hash # Ofrece funciones seguras para hash de contraseñas

try:
    from constants import (
        CLASS_STATUS_ACTIVE,
        CLASS_STATUS_CANCELLED,
        CLASS_STATUSES,
        CREDIT_STATUS_AVAILABLE,
        CREDIT_STATUS_USED,
        ENROLLMENT_CAPACITY_STATUSES,
        ENROLLMENT_PAYMENT_STATUS_PENDING,
        ENROLLMENT_PAYMENT_STATUSES,
        ENROLLMENT_PAYABLE_STATUSES,
        ENROLLMENT_STATUS_CANCELLED,
        ENROLLMENT_STATUS_EXPIRED,
        ENROLLMENT_STATUS_PAID,
        ENROLLMENT_STATUS_PENDING_PAYMENT,
        ENROLLMENT_STATUSES,
        ENROLLMENT_TYPE_SINGLE,
        PAYMENT_METHOD_CARD,
        PAYMENT_METHOD_CASH,
        PAYMENT_METHOD_CREDIT,
        PAYMENT_METHOD_MERCADO_PAGO,
        PAYMENT_METHOD_TRANSFER,
        PAYMENT_METHODS,
        PAYMENT_PRODUCT_TYPES,
        PAYMENT_STATUS_APPROVED,
        PAYMENT_STATUS_EXPIRED,
        PAYMENT_STATUS_PENDING,
        PAYMENT_STATUS_REJECTED,
        PAYMENT_STATUSES,
        PAYMENT_TYPE_FULL,
        PAYMENT_TYPES,
    )
except ModuleNotFoundError:
    from .constants import (
        CLASS_STATUS_ACTIVE,
        CLASS_STATUS_CANCELLED,
        CLASS_STATUSES,
        CREDIT_STATUS_AVAILABLE,
        CREDIT_STATUS_USED,
        ENROLLMENT_CAPACITY_STATUSES,
        ENROLLMENT_PAYMENT_STATUS_PENDING,
        ENROLLMENT_PAYMENT_STATUSES,
        ENROLLMENT_PAYABLE_STATUSES,
        ENROLLMENT_STATUS_CANCELLED,
        ENROLLMENT_STATUS_EXPIRED,
        ENROLLMENT_STATUS_PAID,
        ENROLLMENT_STATUS_PENDING_PAYMENT,
        ENROLLMENT_STATUSES,
        ENROLLMENT_TYPE_SINGLE,
        PAYMENT_METHOD_CARD,
        PAYMENT_METHOD_CASH,
        PAYMENT_METHOD_CREDIT,
        PAYMENT_METHOD_MERCADO_PAGO,
        PAYMENT_METHOD_TRANSFER,
        PAYMENT_METHODS,
        PAYMENT_PRODUCT_TYPES,
        PAYMENT_STATUS_APPROVED,
        PAYMENT_STATUS_EXPIRED,
        PAYMENT_STATUS_PENDING,
        PAYMENT_STATUS_REJECTED,
        PAYMENT_STATUSES,
        PAYMENT_TYPE_FULL,
        PAYMENT_TYPES,
    )

# Creación del Objeto: se crea la instancia global que será usada por todos los modelos. 
db = SQLAlchemy()

# Definición del Modelo de Usuario
class User(UserMixin, db.Model):
    __tablename__ = "users" 

    id = db.Column(db.Integer, primary_key=True) #columna id que es un entero y es la clave primaria (única para cada usuario)
    username = db.Column(db.String(80), nullable=False) #columna username que es una cadena de texto de hasta 80 caracteres, puede haber usuarios con el mismo nombre y no puede ser nula (debe tener un valor)
    apellido = db.Column(db.String(80), nullable=True) # Apellido del usuario
    email = db.Column(db.String(120), unique=True, nullable=False)#columna email que es una cadena de texto de hasta 120 caracteres, también debe ser única y no nula
    dni = db.Column(db.String(20), nullable=True) # DNI del usuario
    telefono = db.Column(db.String(20), nullable=True) # Teléfono del usuario
    password_hash = db.Column(db.String(256), nullable=False)#columna password_hash que es una cadena de texto de hasta 256 caracteres, no puede ser nula, y se usará para almacenar el hash seguro de la contraseña del usuario en lugar de la contraseña en texto plano
    # Campos para el login 2FA de administradores
    admin_login_code = db.Column(db.String(6), nullable=True)
    admin_login_code_expiration = db.Column(db.DateTime, nullable=True)
    role = db.Column(db.String(20), default="client") # Rol del usuario: client, employee, admin
    payments = db.relationship(
        "Payment",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="Payment.user_id",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "apellido": self.apellido,
            "email": self.email,
            "dni": self.dni,
            "telefono": self.telefono,
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
    STATUS_ACTIVE = CLASS_STATUS_ACTIVE
    STATUS_CANCELLED = CLASS_STATUS_CANCELLED
    VALID_STATUSES = CLASS_STATUSES

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    fecha_hora = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False, default=60)
    cupoMaximo = db.Column(db.Integer, nullable=False, default=20)
    id_actividad = db.Column(db.Integer, db.ForeignKey("actividades.id"), nullable=False)
    estado = db.Column(db.String(20), default=STATUS_ACTIVE, nullable=False)
    profesor_id = db.Column(db.Integer, db.ForeignKey("profesores.id"), nullable=False)
    descuento = db.Column(db.Integer, nullable=False, default=0) # Porcentaje de descuento (0, 40, 70)
    room = db.Column(db.String(50), nullable=True)

    # Relación con la actividad (necesaria para el catálogo y respuestas limpias)
    actividad = db.relationship("Actividades", backref="classes")
    profesor = db.relationship("Profesor", backref="classes")
    # Relaciones con inscripciones y asistencias
    enrollments = db.relationship("Enrollment", back_populates="class_", cascade="all, delete-orphan")
    attendances = db.relationship("Attendance", back_populates="class_", cascade="all, delete-orphan")
    profesor = db.relationship("Profesor", backref="classes")
    payments = db.relationship("Payment", back_populates="class_")

    # El gimnasio tiene salones físicos limitados: dos clases no pueden compartir
    # salón en el mismo horario, pero sí pueden coincidir en horario si están en
    # salones distintos (incluida la misma actividad repetida en paralelo).
    __table_args__ = (
        db.UniqueConstraint("fecha_hora", "room", name="horario_salon_unico"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "fecha_hora": self.fecha_hora.isoformat() if self.fecha_hora else None,
            "time": self.fecha_hora.strftime("%H:%M") if self.fecha_hora else "",
            "duration_minutes": self.duration_minutes,
            "cupoMaximo": self.cupoMaximo,
            "actividad_name": self.actividad.name if self.actividad else None,
            "estado": self.estado,
            "profesor_id": self.profesor_id,
            "descuento": self.descuento,
            "room": self.room,
        }


class Enrollment(db.Model):
    """Inscripción de un usuario a una clase y su estado de pago."""
    __tablename__ = "enrollments"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=False)
    tipo = db.Column(db.String(20), default=ENROLLMENT_TYPE_SINGLE, nullable=False)  # 'Mensual' o 'Suelta'
    estado = db.Column(db.String(20), default=ENROLLMENT_STATUS_PENDING_PAYMENT, nullable=False)
    requiere_reembolso = db.Column(db.Boolean, default=False, nullable=False)  # Para reservas tipo 'Suelta'
    total_amount = db.Column(db.Float, nullable=False, default=0)
    paid_amount = db.Column(db.Float, nullable=False, default=0)
    remaining_amount = db.Column(db.Float, nullable=False, default=0)
    payment_status = db.Column(db.String(20), default=ENROLLMENT_PAYMENT_STATUS_PENDING, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    waitlist_promoted_at = db.Column(db.DateTime, nullable=True)  # Seteado cuando la inscripción viene de una promoción de lista de espera

    user = db.relationship("User", backref=db.backref("enrollments", cascade="all, delete-orphan"))
    class_ = db.relationship("Class", back_populates="enrollments")
    payments = db.relationship("Payment", back_populates="enrollment")

    STATUS_PENDING_PAYMENT = ENROLLMENT_STATUS_PENDING_PAYMENT
    STATUS_PAID = ENROLLMENT_STATUS_PAID
    STATUS_EXPIRED = ENROLLMENT_STATUS_EXPIRED
    STATUS_CANCELLED = ENROLLMENT_STATUS_CANCELLED
    PAYMENT_STATUS_PENDING = ENROLLMENT_PAYMENT_STATUS_PENDING
    VALID_PAYMENT_STATUSES = ENROLLMENT_PAYMENT_STATUSES
    VALID_STATUSES = ENROLLMENT_STATUSES
    PAYABLE_STATUSES = ENROLLMENT_PAYABLE_STATUSES
    CAPACITY_STATUSES = ENROLLMENT_CAPACITY_STATUSES

    # Garantizar que un usuario no se inscriba dos veces a la misma clase
    __table_args__ = (db.UniqueConstraint("user_id", "class_id", name="uq_user_class"),)


class WaitlistEntry(db.Model):
    """Entrada de lista de espera por clase."""
    __tablename__ = "waitlists"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    user = db.relationship("User", backref=db.backref("waitlists", cascade="all, delete-orphan"))
    class_ = db.relationship("Class", backref=db.backref("waitlists", cascade="all, delete-orphan"))

    __table_args__ = (
        db.UniqueConstraint("user_id", "class_id", "type", name="uq_waitlist_user_class_type"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "class_id": self.class_id,
            "type": self.type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


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

# ==============================================================================
# Módulo de Cancelaciones, Créditos y Notificaciones
# ==============================================================================

class Credit(db.Model):
    """Crédito reutilizable generado por una clase cancelada."""
    __tablename__ = "creditos"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    activity_id = db.Column("actividad_id", db.Integer, db.ForeignKey("actividades.id"), nullable=False)
    origin_class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=True)
    enrollment_id = db.Column(db.Integer, db.ForeignKey("enrollments.id"), nullable=True)
    expires_at = db.Column("fecha_expiracion", db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    estado = db.Column(db.String(20), default=CREDIT_STATUS_AVAILABLE, nullable=False)
    tipo = db.Column(db.String(20), default=ENROLLMENT_TYPE_SINGLE, nullable=False)

    user = db.relationship("User", backref=db.backref("creditos", cascade="all, delete-orphan"))
    actividad = db.relationship("Actividades")
    origin_class = db.relationship("Class", foreign_keys=[origin_class_id])
    enrollment = db.relationship("Enrollment", foreign_keys=[enrollment_id])

    STATUS_AVAILABLE = CREDIT_STATUS_AVAILABLE
    STATUS_USED = CREDIT_STATUS_USED

    def to_dict(self):
        estado = self.STATUS_USED if self.used else self.estado
        return {
            "id": self.id,
            "user_id": self.user_id,
            "activity_id": self.activity_id,
            "actividad_name": self.actividad.name if self.actividad else None,
            "origin_class_id": self.origin_class_id,
            "origin_class_name": self.origin_class.name if self.origin_class else None,
            "enrollment_id": self.enrollment_id,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "fecha_expiracion": self.expires_at.isoformat() if self.expires_at else None,
            "used": self.used,
            "used_at": self.used_at.isoformat() if self.used_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "estado": estado,
            "tipo": self.tipo,
        }


Credito = Credit

class Profesor(db.Model):
    """Representa a un profesor que puede ser asignado a clases."""
    __tablename__ = "profesores"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    apellido = db.Column(db.String(80), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "apellido": self.apellido,
        }

class Payment(db.Model):
    """Registro base de pagos iniciados desde el sistema."""
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    enrollment_id = db.Column(db.Integer, db.ForeignKey("enrollments.id"), nullable=False)
    # Campo legacy: se conserva por compatibilidad con SQLite/datos anteriores.
    # Los pagos nuevos se relacionan por enrollment_id.
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=True)
    product_type = db.Column(db.String(30), nullable=True)
    payment_type = db.Column(db.String(30), nullable=False, default=PAYMENT_TYPE_FULL)
    payment_method = db.Column(db.String(30), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    discount_percentage = db.Column(db.Integer, nullable=False, default=0)
    final_amount = db.Column(db.Float, nullable=False)
    mercado_pago_preference_id = db.Column(db.String(120), nullable=True)
    mercado_pago_payment_id = db.Column(db.String(120), nullable=True)
    registered_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default=PAYMENT_STATUS_PENDING)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    user = db.relationship("User", back_populates="payments", foreign_keys=[user_id])
    registered_by = db.relationship("User", foreign_keys=[registered_by_user_id])
    enrollment = db.relationship("Enrollment", back_populates="payments")
    class_ = db.relationship("Class", back_populates="payments")

    METHOD_MERCADO_PAGO = PAYMENT_METHOD_MERCADO_PAGO
    METHOD_CARD = PAYMENT_METHOD_CARD
    METHOD_CREDIT = PAYMENT_METHOD_CREDIT
    METHOD_CASH = PAYMENT_METHOD_CASH
    METHOD_TRANSFER = PAYMENT_METHOD_TRANSFER
    VALID_PAYMENT_TYPES = PAYMENT_TYPES
    VALID_PRODUCT_TYPES = PAYMENT_PRODUCT_TYPES
    VALID_PAYMENT_METHODS = PAYMENT_METHODS
    TYPE_FULL = PAYMENT_TYPE_FULL
    STATUS_PENDING = PAYMENT_STATUS_PENDING
    STATUS_APPROVED = PAYMENT_STATUS_APPROVED
    STATUS_REJECTED = PAYMENT_STATUS_REJECTED
    STATUS_EXPIRED = PAYMENT_STATUS_EXPIRED
    VALID_STATUSES = PAYMENT_STATUSES

    def to_dict(self):
        class_obj = self.enrollment.class_ if self.enrollment else self.class_
        return {
            "id": self.id,
            "user_id": self.user_id,
            "enrollment_id": self.enrollment_id,
            "class_id": class_obj.id if class_obj else self.class_id,
            "class_name": class_obj.name if class_obj else None,
            "actividad": class_obj.actividad.name if class_obj and class_obj.actividad else None,
            "product_type": self.product_type,
            "payment_type": self.payment_type,
            "payment_method": self.payment_method,
            "amount": self.amount,
            "discount_percentage": self.discount_percentage,
            "final_amount": self.final_amount,
            "mercado_pago_preference_id": self.mercado_pago_preference_id,
            "mercado_pago_payment_id": self.mercado_pago_payment_id,
            "registered_by_user_id": self.registered_by_user_id,
            "notes": self.notes,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SystemSetting(db.Model):
    """Configuraciones globales del sistema."""
    __tablename__ = "system_settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(120), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "key": self.key,
            "value": self.value,
        }
