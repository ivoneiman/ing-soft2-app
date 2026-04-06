# Módulo 1: Usuarios y Autenticación

## 1. Descripción general
Este módulo gestiona el registro, login, logout y consulta del usuario actual. Es la base de seguridad y acceso para el resto del sistema.

## 2. Requerimientos funcionales
- Registro de usuario con email, username y contraseña.
- Login de usuario con email y contraseña.
- Logout de usuario.
- Consulta del usuario autenticado ("/me").
- Enlaces entre login y registro en el frontend.

## 3. Diseño de datos
Modelo principal:

```python
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
```

## 4. Endpoints/API
| Método | Ruta           | Auth | Descripción         |
|--------|----------------|------|---------------------|
| POST   | /api/register  | ❌   | Crear cuenta        |
| POST   | /api/login     | ❌   | Iniciar sesión      |
| POST   | /api/logout    | ✅   | Cerrar sesión       |
| GET    | /api/me        | ✅   | Usuario actual      |

## 5. Lógica y algoritmos clave
- Validación de campos requeridos en backend.
- Hash de contraseña al registrar usuario.
- Verificación de contraseña al loguear.
- Manejo de sesión con Flask-Login.
- Manejo de errores y mensajes en frontend.

## 6. Decisiones de diseño
- Se utiliza Flask-Login para manejo de sesión.
- El modelo User es simple, sin relaciones ni campos extra.
- El frontend usa Vue Router y Axios para navegación y llamadas a la API.
- Se agregan enlaces entre login y registro para mejorar la UX.

## 7. Pendientes y mejoras futuras
- Agregar validaciones más avanzadas (fuerza de contraseña, email válido).
- Permitir recuperación de contraseña.
- Agregar roles y permisos.
- Mejorar feedback visual en el frontend.

## 8. Historial de cambios
- 2026-04-05: Creación del módulo y documentación inicial.
- 2026-04-05: Implementación de login, registro, logout y consulta de usuario actual.
