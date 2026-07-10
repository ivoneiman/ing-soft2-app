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

### Backend

- **Python 3**: lenguaje principal utilizado para desarrollar la API del sistema.
- **Flask**: framework web usado para definir rutas, recibir requests y responder al frontend.
- **Flask-SQLAlchemy**: librería que permite trabajar con la base de datos usando modelos de Python.
- **SQLite**: base de datos local utilizada para desarrollo y pruebas.
- **Flask-Login**: dependencia utilizada como apoyo para el modelo de usuario y manejo de autenticación.
- **Flask-CORS**: permite que el frontend Vue pueda comunicarse con el backend Flask durante el desarrollo local.
- **Werkzeug**: se utiliza para generar y verificar hashes de contraseñas.
- **python-dotenv**: carga variables de entorno desde archivos `.env`.
- **Mercado Pago SDK**: integración con Mercado Pago Checkout Pro para crear preferencias de pago.
- **Resend**: servicio usado para enviar emails transaccionales, por ejemplo códigos de login admin o avisos de clases canceladas.
- **tzdata**: soporte de zonas horarias para cálculos relacionados con fechas, descuentos y vencimientos.

### Frontend

- **Vue 3**: framework utilizado para construir la interfaz de usuario como una SPA.
- **Vue Router**: manejo de rutas y navegación dentro del frontend.
- **Vite**: herramienta de desarrollo y build del frontend.
- **Axios**: cliente HTTP utilizado para consumir la API del backend.
- **qrcode.vue**: componente usado para generar códigos QR desde Vue.
- **html5-qrcode**: librería utilizada para escanear códigos QR desde la cámara.
- **JavaScript, HTML y CSS**: base del desarrollo del frontend.


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

- `SECRET_KEY`: clave utilizada por Flask para sesiones.
- `SQLALCHEMY_DATABASE_URI`: URL de conexión a la base de datos. Por defecto se usa SQLite.
- `CORS_ORIGINS`: orígenes permitidos para el frontend local y el deploy de develop.
- `ENVIRONMENT`: entorno de ejecución, por ejemplo `development`.
- `FLASK_DEBUG`: activa o desactiva el modo debug en desarrollo.
- `MERCADOPAGO_PUBLIC_KEY`: clave pública de Mercado Pago.
- `MERCADOPAGO_ACCESS_TOKEN`: token usado por el SDK de Mercado Pago.
- `MERCADOPAGO_CHECKOUT_MODE`: modo de checkout, por ejemplo `sandbox`.
- `MERCADOPAGO_TEST_PAYER_EMAIL`: email opcional para pruebas sandbox.
- `PUBLIC_BACKEND_URL`: URL pública base del backend para Mercado Pago, por ejemplo la URL HTTPS de Cloudflare Tunnel o ngrok, sin barra final.
- `PAYMENT_SUCCESS_URL`: override opcional de retorno para pagos aprobados.
- `PAYMENT_FAILURE_URL`: override opcional de retorno para pagos fallidos.
- `PAYMENT_PENDING_URL`: override opcional de retorno para pagos pendientes.
- `MERCADOPAGO_NOTIFICATION_URL`: override opcional del webhook para confirmar pagos automáticamente.
- `MERCADOPAGO_WEBHOOK_SECRET`: secreto de firma del webhook configurado en el panel de Mercado Pago. Es obligatorio en producción.
- `FRONTEND_PAYMENTS_URL`: URL del frontend donde se muestra el resultado del pago. Para develop: `https://ing-soft2-app-git-develop-ivoneimans-projects.vercel.app/pagos`.
- `GYM_SITE_URL`: URL base del frontend para links en emails. Para develop: `https://ing-soft2-app-git-develop-ivoneimans-projects.vercel.app`.
- `RESEND_API_KEY`: API key de Resend para envío de emails.
- `EMAIL_FROM`: remitente utilizado en emails transaccionales.
- `APP_TIMEZONE`: zona horaria usada para fechas y reglas de descuento.
- `LOG_LEVEL`: nivel de logs del backend.

El frontend puede usar:

- `VITE_API_URL`: URL base de la API. Si no se define, usa `http://localhost:5000/api`.

No se deben commitear credenciales reales.

### Retorno desde Mercado Pago en desarrollo

Mercado Pago Checkout Pro no debe recibir `localhost` ni `127.0.0.1` en `back_urls` cuando se usa `auto_return`. Para probar en local hay que exponer el backend con una URL HTTPS pública.

Flujo recomendado con Cloudflare Tunnel:

1. Levantar el backend local en `http://localhost:5000`.
2. Levantar el túnel apuntando al backend, por ejemplo `cloudflared tunnel --url http://localhost:5000`.
3. Copiar la URL HTTPS generada por Cloudflare en `backend/.env`:

```env
PUBLIC_BACKEND_URL=https://tu-url.trycloudflare.com
MERCADOPAGO_WEBHOOK_SECRET=tu-secreto-de-firma-del-webhook
FRONTEND_PAYMENTS_URL=https://ing-soft2-app-git-develop-ivoneimans-projects.vercel.app/pagos
GYM_SITE_URL=https://ing-soft2-app-git-develop-ivoneimans-projects.vercel.app
```

Con `PUBLIC_BACKEND_URL`, el backend arma automáticamente:

- `https://tu-url.trycloudflare.com/api/payments/return/success`
- `https://tu-url.trycloudflare.com/api/payments/return/failure`
- `https://tu-url.trycloudflare.com/api/payments/return/pending`
- `https://tu-url.trycloudflare.com/api/payments/webhook`

Si Cloudflare genera una URL nueva, solo hay que actualizar `PUBLIC_BACKEND_URL` y reiniciar Flask.

El webhook (`/api/payments/webhook`) es la única fuente de verdad que consulta la API de Mercado Pago y actualiza la inscripción/pago. Los `back_urls` únicamente devuelven al navegador a `Mis Clases` o `Actividades`; cerrar la pestaña o no recibir el retorno no impide la confirmación. Todas las URLs de retorno y webhook deben ser públicas y HTTPS: el backend rechaza una preferencia configurada con `localhost` para evitar pagos que queden pendientes silenciosamente.

## Funcionalidades principales

- Usuarios y roles: registro, inicio, cierre de sesión, creación de usuarios, login especial para admins, etc.
- Actividades y clases: listados, reportes, creación de clases, control de cupos, aplicación de descuentos, sistema de cancelaciones, etc.
- Inscripciones: usuarios a clases, estados según pago y vencimiento, consultas.
- Pagos y señas: creación de pagos con Mercado Pago Checkout Pro, registros, historiales, sistema de señas, etc.
- Asistencia por QR: generación de QR por user, registros de asistencia, consultas en vivo, validación de inscripción y pago para permitir asistir.
- Créditos y cancelaciones: cancelaciones de clases, generan créditos reutilizables cuando corresponde. Consulta de créditos, notificaciones internas y externas (mail) para usuarios, etc.
- Notificaciones e emails: Notificaciones internas y externas (email) sobre cancelaciones de clases y generaciones de créditos.

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
