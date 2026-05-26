# INGE2-APP — Flask + Vue.js + SQLite (QR Attendance System)

Sistema de gestión de asistencia mediante códigos QR con autenticación de usuarios.

## Stack
- **Backend:** Python + Flask + SQLAlchemy (SQLite)
- **Frontend:** Vue 3 + Vue Router + Axios
- **QR:** qrcode.vue + html5-qrcode
- **Autenticación:** Flask-Login + SessionHTTP

---

## Setup Rápido

### Opción 1: Script Automático (Recomendado para Windows)

```bash
# En la raíz del proyecto
git clone <repo-url>
cd ing-soft2-app
python backend/seed.py
cd frontend && npm install
npm run dev
```

En otra terminal:
```bash
cd backend
pip install -r requirements.txt
python app.py
```

### Opción 2: Paso a Paso

#### Backend

```bash
# 1. Ir al directorio del backend
cd backend

# 2. Crear entorno virtual (solo la primera vez)
python -m venv venv

# 3. Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Crear base de datos y datos de prueba
python seed.py

# 6. Levantar servidor (debería mostrar "Running on http://localhost:5000")
python app.py
```

#### Frontend (en otra terminal)

```bash
# 1. Ir al directorio del frontend
cd frontend

# 2. Instalar dependencias
npm install

# 3. Levantar servidor (debería abrir en http://localhost:5173)
npm run dev
```

---

## Validar Setup

Si todo funciona correctamente deberías ver:

✅ **Backend**: "Running on http://localhost:5000"
✅ **Frontend**: "Local: http://localhost:5173"
✅ **Base de datos**: archivo `backend/app.db` creado
✅ **Seed**: mensaje "✅ SEED COMPLETADO EXITOSAMENTE"

---

## Credenciales de Prueba (después de ejecutar `seed.py`)

Usa cualquiera de estas cuentas para testear:

| Email | Contraseña | Rol |
|-------|-----------|-----|
| admin@test.com | admin123 | admin |
| employee@test.com | employee123 | employee |
| client@test.com | client123 | client |

---

## Datos de Prueba Incluidos

Al ejecutar `seed.py` se crean automáticamente:

- ✓ **3 usuarios** con diferentes roles (admin, employee, client)
- ✓ **3 clases** de ejemplo (Ingeniería de Software 2, Programación Avanzada, Bases de Datos)
- ✓ **Enrollments** (inscripciones de usuarios a clases)
- ✓ Sistema de **asistencia mediante QR** listo para usar

---

## Flujo de Funcionalidades

### 1. Autenticación
- Login/Logout
- Registro de nuevos usuarios
- Roles basados en acceso

### 2. Clases
- Ver clases disponibles
- Inscribirse a clases
- Ver mis inscripciones

### 3. Asistencia por QR
- Generar código QR para clase
- Escanear código QR para marcar asistencia
- Ver historial de asistencias

### 4. Dashboard
- Panel personalizado por rol
- Estadísticas de asistencia
- Información del usuario

---

## Estructura del Proyecto

```
ing-soft2-app/
├── backend/
│   ├── app.py                  ← Servidor Flask + rutas API
│   ├── email_service.py        ← Envío de emails transaccionales con Resend
│   ├── models.py               ← Modelos SQLAlchemy (User, Class, Enrollment, Attendance)
│   ├── seed.py                 ← Datos de prueba (IMPORTANTE)
│   ├── requirements.txt         ← Dependencias Python
│   ├── .env.example            ← Variables de entorno de ejemplo
│   ├── app.db                  ← Base de datos SQLite (generada al ejecutar seed.py)
│   └── instance/
│
├── frontend/
│   ├── package.json            ← Dependencias Node.js
│   ├── vite.config.js          ← Configuración Vite
│   ├── index.html              ← Entry point HTML
│   ├── src/
│   │   ├── App.vue             ← Componente raíz
│   │   ├── main.js             ← Entry point
│   │   ├── router/
│   │   │   └── index.js        ← Rutas (login, dashboard, etc)
│   │   ├── views/
│   │   │   ├── auth/           ← LoginView, RegisterView
│   │   │   ├── dashboard/      ← DashboardView
│   │   │   ├── actividades/    ← QR scanner y generador
│   │   │   └── ...
│   │   ├── components/         ← Componentes reutilizables
│   │   ├── services/
│   │   │   ├── api.js          ← Cliente HTTP (axios)
│   │   │   └── authStore.js    ← Autenticación
│   │   └── utils/
│   │       └── roleHelpers.js  ← Utilidades de roles
│   │
│   └── public/
│       └── robots.txt
│
├── docs/                        ← Documentación del proyecto
│   ├── epicas-historias-usuario/
│   ├── flujo-trabajo/
│   └── uml/
│
└── README.md                    ← Este archivo
```

---

## Troubleshooting (problemas)

### Backend no levanta

**Error: "ModuleNotFoundError: No module named 'flask'"**
```bash
# Solución: Asegurar que el venv está activado
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Reinstalar dependencias
pip install -r requirements.txt
```

**Error: "Address already in use :5000"**
```bash
# Puerto ya está en uso. Matar el proceso o usar otro puerto:
python app.py --port 5001
```

### Frontend no levanta

**Error: "npm: command not found"**
```bash
# Solución: Instalar Node.js desde https://nodejs.org/
# Luego en terminal nueva:
npm install
npm run dev
```

**Error: "Cannot GET /api/..."**
```bash
# Solución: Verificar que backend está corriendo en http://localhost:5000
# El frontend redirige /api a http://localhost:5000/api automáticamente
```

### Base de datos no se crea

**Error: "No module named 'app'"**
```bash
# Solución: Asegurar estar en directorio backend/
cd backend
python seed.py
```

**Error: "UNIQUE constraint failed"**
```bash
# Solución: Base de datos existe con datos previos
# Opción 1: Borrar app.db y ejecutar seed.py nuevamente
# Opción 2: Ejecutar seed.py nuevamente (es idempotente, no duplica datos)
```

---

## Variables de Entorno

Crear archivo `.env` en `backend/` basado en `.env.example`:

```bash
# backend/.env
SECRET_KEY=dev-secret-key
CORS_ORIGINS=http://localhost:5173
ENVIRONMENT=development

# Mercado Pago
MERCADOPAGO_PUBLIC_KEY=
MERCADOPAGO_ACCESS_TOKEN=
MERCADOPAGO_CHECKOUT_MODE=sandbox

# Emails transaccionales con Resend
RESEND_API_KEY=
EMAIL_FROM=onboarding@resend.dev
```

### Emails con Resend

El sistema usa Resend para enviar emails cuando una clase se cancela. Además de crear las notificaciones internas y los créditos reutilizables, el backend intenta enviar emails al usuario afectado.

Para probar emails en desarrollo:

1. Crear una cuenta gratuita en [Resend](https://resend.com/).
2. Crear una API key.
3. Copiar `backend/.env.example` a `backend/.env`.
4. Completar:

```env
RESEND_API_KEY=tu_api_key_de_resend
EMAIL_FROM=onboarding@resend.dev
```

Cada integrante del equipo debe usar su propia API key en su `.env` local. No commitear claves reales.

Nota: `onboarding@resend.dev` sirve para pruebas. Para enviar desde un remitente propio en producción hace falta verificar un dominio en Resend.

---

## APIs Backend Principales

### Autenticación
- `POST /api/login` - Login de usuario
- `POST /api/logout` - Logout
- `POST /api/register` - Registro de usuario
- `GET /api/me` - Obtener usuario actual

### Clases y Asistencia
- `POST /api/attendance/register` - Registrar asistencia (QR)
- `GET /api/classes` - Listar clases (a implementar)
- `GET /api/enrollments` - Listar inscripciones (a implementar)

Ver `backend/app.py` para documentación completa de endpoints.

---

## 📝 Comandos Útiles

```bash
# Limpiar base de datos (ejecutar seed.py nuevamente)
rm backend/app.db
python backend/seed.py

# Ver logs del backend en tiempo real
python backend/app.py  # Ya está en modo debug

# Actualizar dependencias
pip install -r requirements.txt --upgrade
npm update

# Verificar versiones instaladas
python --version
node --version
npm --version
```

---

## Contribuir

Antes de commitear cambios:

1. ✅ Verificar que `seed.py` funciona correctamente
2. ✅ Verificar que backend y frontend levantan sin errores
3. ✅ Tester con datos de prueba incluidos
4. ✅ Actualizar `.env.example` si agregas nuevas variables

---

## 📄 Licencia

Proyecto educativo - INGE2 (Ingeniería de Software 2)

---

## Ayuda

Si encontras problemas:

1. **Revisar este README** - Probablemente la solución está en "Troubleshooting"
2. **Revisar logs de error** - Terminal muestra información del error
3. **Ejecutar seed.py nuevamente** - Crea datos faltantes automáticamente
4. **Borrar app.db y comenzar de nuevo** - Último recurso para limpiar estado

---

**Última actualización:** Mayo 2024

    │   └── views/
    │       ├── LoginView.vue
    │       └── RegisterView.vue
    ├── index.html
    └── vite.config.js
```

---

## 🔌 API Endpoints

| Método | Ruta             | Auth | Descripción              |
|--------|------------------|------|--------------------------|
| POST   | /api/register    | ❌   | Crear cuenta             |
| POST   | /api/login       | ❌   | Iniciar sesión           |
| POST   | /api/logout      | ✅   | Cerrar sesión            |
| GET    | /api/me          | ✅   | Usuario actual           |

---

## 🧪 Probar la API con curl
```bash
# Registrar usuario
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{"username":"juan","email":"juan@test.com","password":"1234"}' \
  -c cookies.txt

# Ver usuario actual (usa la cookie de sesión)
curl http://localhost:5000/api/me -b cookies.txt
```
