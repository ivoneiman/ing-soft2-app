# SiempreGym

Trabajo integrador realizado para la materia **Ingeniería de Software 2**.

SiempreGym es un sistema web para la administración básica de un gimnasio. Permite gestionar usuarios, actividades, clases, inscripciones, pagos, señas, asistencia por QR, cancelaciones, créditos y notificaciones.

## Grupo e integrantes

**Grupo 9**

- Ivo Joaquín Neiman
- Facundo Casco
- Carlos Cristian Berruti
- Tobías Gonzales
- Franco Martín

## Tecnologías utilizadas

**Backend**

- Python 3
- Flask
- Flask-SQLAlchemy
- Flask-Login
- Flask-CORS
- SQLite
- Mercado Pago SDK
- Resend
- python-dotenv
- Werkzeug

**Frontend**

- Vue 3
- Vue Router
- Vite
- Axios
- qrcode.vue
- html5-qrcode
- JavaScript, HTML y CSS

## Usuarios de prueba

Después de ejecutar el seed, se pueden usar estas cuentas:

| Rol | Email | Contraseña |
| --- | --- | --- |
| Administrador | `admin@test.com` | `admin123` |
| Empleado | `employee@test.com` | `employee123` |
| Cliente | `client@test.com` | `client123` |

## Instalación y ejecución

**Backend**

```bash
cd backend
pip install -r requirements.txt
python seed.py
python app.py
```

Backend local:

```text
http://localhost:5000
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

Frontend local:

```text
http://localhost:5173
```

También existen scripts de ayuda para preparar el entorno:

```bash
setup.bat
./setup.sh
```

## Variables de entorno

El backend usa un archivo `.env` dentro de `backend/`. Se puede tomar como base `backend/.env.example`.

Variables principales:

- `SECRET_KEY`
- `SQLALCHEMY_DATABASE_URI`
- `CORS_ORIGINS`
- `MERCADOPAGO_PUBLIC_KEY`
- `MERCADOPAGO_ACCESS_TOKEN`
- `MERCADOPAGO_CHECKOUT_MODE`
- `MERCADOPAGO_TEST_PAYER_EMAIL`
- `PAYMENT_SUCCESS_URL`
- `PAYMENT_FAILURE_URL`
- `PAYMENT_PENDING_URL`
- `FRONTEND_PAYMENTS_URL`
- `RESEND_API_KEY`
- `EMAIL_FROM`
- `APP_TIMEZONE`

El frontend puede usar:

- `VITE_API_URL`

No se deben commitear credenciales reales.

## Funcionalidades principales

- Usuarios y roles.
- Actividades y clases.
- Inscripciones.
- Pagos y señas.
- Asistencia por QR.
- Créditos y cancelaciones.
- Notificaciones y emails.

## Arquitectura general

El proyecto está separado en dos partes:

- `backend/`: API desarrollada con Flask.
- `frontend/`: SPA desarrollada con Vue.

El frontend se comunica con el backend mediante una REST API. En el backend, parte de la lógica del sistema está organizada en `services/`, separando responsabilidades como pagos, inscripciones, clases, créditos, cancelaciones y notificaciones.

## Seguridad y validaciones

El sistema incluye autenticación con sesiones, roles de usuario, hash de contraseñas con Werkzeug, validaciones desde el backend y control de acceso para operaciones administrativas.

También se usa SQLAlchemy para trabajar con la base de datos y variables de entorno para no dejar credenciales sensibles dentro del código.

## Testing y smoke tests

Validación general del entorno:

```bash
python validate_setup.py
```

Smoke test de pagos parciales:

```bash
cd backend
python smoke_partial_payments.py
```

Durante el desarrollo también se realizaron pruebas E2E sobre pagos con Mercado Pago en sandbox, validando el lifecycle de pagos, señas, saldos, QR y partial payments.
