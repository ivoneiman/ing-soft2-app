from flask_sqlalchemy import SQLAlchemy #SQLAlchemy es un Object-Relational Mapper que traduce objetos Python a tablas SQL y viceversa.
from flask_login import UserMixin #Permite heredar funcionalidades de gestión de usuarios (como autenticación y sesiones) en la clase User.
from werkzeug.security import generate_password_hash, check_password_hash #ofrece funciones seguras para hash de contraseñas

# Creación del Objeto: se crea la instancia global que será usada por todos los modelos. 
# En app.py se llama a db.init_app(app) para asociarla con la aplicación Flask, 
# lo que permite usar SQLAlchemy para interactuar con la base de datos a través de esta instancia.
db = SQLAlchemy()

#Definición del Modelo de Usuario: se define la clase User que hereda de UserMixin (para funcionalidades de autenticación) 
# y db.Model (para mapear a una tabla SQL).
class User(UserMixin, db.Model):
    __tablename__ = "users" #nombre de la tabla en la base de datos, se llama "users" y tendrá las columnas definidas a continuación

    id = db.Column(db.Integer, primary_key=True) #columna id que es un entero y es la clave primaria (única para cada usuario)
    username = db.Column(db.String(80), unique=True, nullable=False) #columna username que es una cadena de texto de hasta 80 caracteres, debe ser única (no puede haber dos usuarios con el mismo username) y no puede ser nula (debe tener un valor)
    email = db.Column(db.String(120), unique=True, nullable=False)#columna email que es una cadena de texto de hasta 120 caracteres, también debe ser única y no nula
    password_hash = db.Column(db.String(256), nullable=False)#columna password_hash que es una cadena de texto de hasta 256 caracteres, no puede ser nula, y se usará para almacenar el hash seguro de la contraseña del usuario en lugar de la contraseña en texto plano

    #métodos auxiliares del modelo
    # set_password: toma una contraseña en texto plano, genera un hash seguro usando generate_password_hash y lo almacena en la columna password_hash.
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # check_password: toma una contraseña en texto plano, genera un hash seguro usando generate_password_hash y lo compara con el hash almacenado en la columna password_hash.
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # to_dict: devuelve un diccionario con los datos del usuario (id, username y email)
    # que se puede usar para convertir a JSON en las respuestas de la API.
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
        }
