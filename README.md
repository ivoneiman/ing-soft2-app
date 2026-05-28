# SiempreGym

Trabajo integrador realizado para la materia **Ingeniería de Software 2**.

**Grupo 9**

## Integrantes

- Ivo Joaquín Neiman
- Facundo Casco
- Carlos Cristian Berruti
- Tobías Gonzales
- Franco Martín

## Descripción general

SiempreGym es un sistema web pensado para administrar el funcionamiento básico de un gimnasio. El proyecto permite organizar actividades, crear clases, gestionar usuarios con distintos roles, registrar inscripciones, controlar pagos y marcar asistencia mediante códigos QR.

La aplicación también incluye funcionalidades administrativas como cancelación de clases, generación de créditos reutilizables, historial de pagos, notificaciones internas, envío de emails y pagos online mediante Mercado Pago Checkout Pro.

El objetivo del sistema es centralizar tareas que normalmente se hacen de forma manual: anotar alumnos, revisar cupos, controlar pagos pendientes, confirmar asistencias y avisar cambios importantes a los usuarios.

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

### Herramientas

- **Git y GitHub**: control de versiones y colaboración del grupo.
- **npm**: instalación y ejecución de dependencias del frontend.
- **pip**: instalación de dependencias del backend.

## Arquitectura general

El proyecto está separado en dos partes principales:

- `backend/`: API desarrollada con Flask. Contiene rutas, modelos, configuración de base de datos, integración con Mercado Pago, envío de emails y servicios de dominio.
- `frontend/`: aplicación SPA desarrollada con Vue. Contiene vistas, layouts, componentes, router y servicios para consumir la API.

La comunicación entre ambas partes se realiza mediante una **REST API**. El frontend envía requests HTTP al backend usando Axios, y el backend responde con datos en formato JSON.

Dentro del backend se incorporó una separación por servicios en `backend/services/`. Estos archivos agrupan lógica relacionada con clases, inscripciones, pagos, créditos, cancelaciones, notificaciones y fechas. Esta organización ayuda a que `app.py` no concentre toda la lógica del sistema y permite que algunas reglas importantes queden mejor separadas.

## Seguridad y validaciones

El sistema incluye varias medidas básicas de seguridad acordes al alcance del proyecto:

- Autenticación de usuarios mediante login y sesiones.
- Hash de contraseñas con Werkzeug, evitando guardar contraseñas en texto plano.
- Roles de usuario: `client`, `employee` y `admin`.
- Restricciones de acceso en endpoints administrativos.
- Validaciones de datos desde el backend antes de crear usuarios, clases, inscripciones o pagos.
- Uso de SQLAlchemy para evitar construir consultas SQL manuales en las operaciones principales.
- Configuración CORS para permitir la comunicación con el frontend local.
- Escape de contenido dinámico en emails generados desde el backend.
- Variables sensibles fuera del código fuente mediante archivos `.env`.

Como mejora futura, se podría reforzar la protección CSRF para endpoints que usan cookies de sesión, especialmente si el sistema se despliega fuera de un entorno académico o de pruebas.

## Funcionalidades principales

### Usuarios y roles

- Registro e inicio de sesión.
- Cierre de sesión.
- Consulta del usuario actual.
- Creación de usuarios desde perfiles administrativos.
- Login especial para administradores con código enviado por email.
- Roles diferenciados para clientes, empleados y administradores.

### Actividades y clases

- Listado de actividades disponibles.
- Consulta de clases por actividad.
- Catálogo de clases.
- Disponibilidad por día y actividad.
- Creación de clases.
- Control de cupos.
- Aplicación de descuentos sobre clases.
- Cancelación de clases por parte de staff.

### Inscripciones

- Inscripción de usuarios a clases.
- Estados de inscripción según pago y vencimiento.
- Inscripciones sueltas o mensuales.
- Consulta de inscripciones pendientes.
- Reapertura o control de inscripciones vencidas/canceladas según reglas del sistema.

### Pagos

- Creación de pagos con Mercado Pago Checkout Pro.
- Registro de pagos manuales por parte de administración.
- Pago completo.
- Pago con seña y saldo restante.
- Historial de pagos.
- Estados de pago: pendiente, aprobado, rechazado y vencido.
- Validaciones para evitar sobrepagos.
- Redirección de retorno desde Mercado Pago.

### Asistencia por QR

- Generación de QR para asistencia.
- Escaneo de QR desde el frontend.
- Registro de asistencia.
- Consulta de asistencia por clase.
- Validación de inscripción y estado de pago antes de permitir asistencia.

### Cancelaciones, créditos y notificaciones

- Cancelación de clases.
- Generación de créditos reutilizables cuando corresponde.
- Consulta de créditos disponibles del usuario.
- Notificaciones internas para usuarios.
- Configuración del mensaje de notificación.
- Emails por cancelación de clase y generación de crédito.

## Instalación y ejecución

### Requisitos previos

- Python 3 instalado.
- Node.js y npm instalados.
- Git instalado.

### Backend

Desde la raíz del proyecto:

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python seed.py
python app.py
```

En Linux/Mac, la activación del entorno virtual es:

```bash
source venv/bin/activate
```

El backend queda disponible en:

```text
http://localhost:5000
```

### Frontend

En otra terminal:

```bash
cd frontend
npm install
npm run dev
```

El frontend queda disponible en:

```text
http://localhost:5173
```

### Setup automático

El repositorio también incluye scripts de ayuda:

```bash
setup.bat
```

o en Linux/Mac:

```bash
./setup.sh
```

Estos scripts preparan el entorno del backend e inicializan datos de prueba. Luego se puede levantar frontend y backend manualmente. En Windows, también se puede usar desde `frontend/`:

```bash
npm run dev:all
```

## Variables de entorno

El backend utiliza un archivo `.env` dentro de `backend/`. Se puede tomar como base `backend/.env.example`.

Variables principales:

- `SECRET_KEY`: clave utilizada por Flask para sesiones.
- `SQLALCHEMY_DATABASE_URI`: URL de conexión a la base de datos. Por defecto se usa SQLite.
- `CORS_ORIGINS`: origen permitido para el frontend local.
- `ENVIRONMENT`: entorno de ejecución, por ejemplo `development`.
- `FLASK_DEBUG`: activa o desactiva el modo debug en desarrollo.
- `MERCADOPAGO_PUBLIC_KEY`: clave pública de Mercado Pago.
- `MERCADOPAGO_ACCESS_TOKEN`: token usado por el SDK de Mercado Pago.
- `MERCADOPAGO_CHECKOUT_MODE`: modo de checkout, por ejemplo `sandbox`.
- `MERCADOPAGO_TEST_PAYER_EMAIL`: email opcional para pruebas sandbox.
- `PAYMENT_SUCCESS_URL`: URL de retorno para pagos aprobados.
- `PAYMENT_FAILURE_URL`: URL de retorno para pagos fallidos.
- `PAYMENT_PENDING_URL`: URL de retorno para pagos pendientes.
- `FRONTEND_PAYMENTS_URL`: URL del frontend donde se muestra el resultado del pago.
- `RESEND_API_KEY`: API key de Resend para envío de emails.
- `EMAIL_FROM`: remitente utilizado en emails transaccionales.
- `APP_TIMEZONE`: zona horaria usada para fechas y reglas de descuento.
- `LOG_LEVEL`: nivel de logs del backend.

El frontend puede usar:

- `VITE_API_URL`: URL base de la API. Si no se define, usa `http://localhost:5000/api`.

No se deben commitear credenciales reales en el repositorio.

## Usuarios de prueba

Al ejecutar:

```bash
python backend/seed.py
```

se crean usuarios demo para probar el sistema:

| Rol | Email | Contraseña |
| --- | --- | --- |
| Administrador | `admin@test.com` | `admin123` |
| Empleado | `employee@test.com` | `employee123` |
| Cliente | `client@test.com` | `client123` |

El seed también carga actividades, clases, inscripciones y ejemplos de pagos/créditos para facilitar las pruebas iniciales.

## Testing y validaciones

El proyecto incluye scripts y pruebas de validación para revisar que el entorno y algunos flujos importantes funcionen correctamente.

### Validación de setup

Desde la raíz:

```bash
python validate_setup.py
```

Este script revisa estructura del proyecto, dependencias, base de datos y puertos principales.

### Smoke test de pagos parciales

Desde `backend/`:

```bash
python smoke_partial_payments.py
```

Este smoke test valida un flujo importante del sistema:

- creación de una inscripción;
- pago de seña;
- bloqueo de asistencia QR mientras el pago está incompleto;
- registro del saldo restante;
- rechazo de sobrepagos;
- aprobación final de la inscripción;
- asistencia permitida una vez completado el pago;
- consistencia del historial de pagos.

### Pruebas E2E y sandbox

Durante el desarrollo se realizaron validaciones de punta a punta sobre el flujo de pagos, usando el entorno sandbox de Mercado Pago. Estas pruebas ayudaron a revisar:

- creación de preferencias de pago;
- retornos desde Mercado Pago;
- lifecycle de pagos pendientes, aprobados, rechazados y vencidos;
- pagos completos, señas y saldos;
- integración entre pagos, inscripciones y asistencia QR;
- comportamiento de partial payments;
- validaciones para evitar estados inconsistentes.

## Estructura del proyecto

```text
ing-soft2-app/
├── backend/
│   ├── app.py
│   ├── models.py
│   ├── constants.py
│   ├── seed.py
│   ├── requirements.txt
│   ├── smoke_partial_payments.py
│   ├── mercadopago_config.py
│   ├── email_service.py
│   └── services/
│       ├── cancellation_service.py
│       ├── class_service.py
│       ├── credit_service.py
│       ├── datetime_service.py
│       ├── enrollment_service.py
│       ├── notification_service.py
│       └── payment_service.py
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── router/
│       ├── services/
│       ├── views/
│       ├── layouts/
│       ├── components/
│       ├── constants/
│       └── utils/
│
├── docs/
├── setup.bat
├── setup.sh
├── validate_setup.py
└── README.md
```

## Documentación complementaria

La carpeta `docs/` contiene material adicional del proyecto, como guías de setup, checklist, documentación de usuarios, flujo de trabajo, validaciones y diagramas UML.

Algunos archivos útiles:

- `docs/QUICK_START.md`
- `docs/SETUP_STEP_BY_STEP.md`
- `docs/CHECKLIST.md`
- `docs/POLITICA_SETUP_BD.md`
- `docs/VALIDACION_FINAL.md`
- `docs/uml/`

## Notas finales

SiempreGym fue desarrollado como proyecto académico para aplicar contenidos de Ingeniería de Software 2 en un sistema concreto. La aplicación busca mostrar un flujo completo de administración de gimnasio, integrando frontend, backend, base de datos, pagos, roles, asistencia y notificaciones.

Para continuar el desarrollo, se recomienda revisar el README, levantar el entorno local, ejecutar el seed y probar los usuarios demo antes de modificar funcionalidades existentes.
