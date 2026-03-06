# Demo IS2 — Flask + Vue.js + PostgreSQL

Proyecto demo con autenticación de usuarios y CRUD básico de notas.
Guía instalación: https://docs.google.com/document/d/1gyVWPFO2TZeU4UhWOwTB-A5zzbg9iM2y/edit?pli=1

## Stack
- **Backend:** Python + Flask + Flask-Login + SQLAlchemy
- **Frontend:** Vue 3 + Vue Router + Axios
- **DB:** PostgreSQL

---

## ⚙️ Setup del backend

### 1. Crear y activar entorno virtual
```bash
cd backend
python -m venv venv

# Linux / Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

> ⚠️ Si usás Python 3.14+, `psycopg2-binary` no es compatible. El `requirements.txt` ya usa `psycopg[binary]` que sí funciona.

### 3. Configurar variables de entorno
```bash
cp .env.example .env
# Editá .env con tu contraseña de PostgreSQL
```

El archivo `.env` tiene que quedar así:
```
DATABASE_URL=postgresql+psycopg://postgres:TU_PASSWORD@localhost:5432/demo_db
```

> ⚠️ Usá `postgresql+psycopg://` (no `postgresql://`). Si usás la URL vieja el backend no va a conectar.

### 4. Crear la base de datos en PostgreSQL
```bash
psql -U postgres
```
```sql
CREATE DATABASE demo_db;
\q
```

> 💡 En Windows, si `psql` no se reconoce, agregá `C:\Program Files\PostgreSQL\<version>\bin` al PATH del sistema y reiniciá la terminal.

### 5. Levantar el servidor
```bash
python app.py
```

✅ El backend crea las tablas automáticamente al arrancar.  
✅ Disponible en http://localhost:5000

#### (Opcional) Poblar con datos de prueba
```bash
python seed.py
# Usuario de prueba: test@example.com / password123
```

---

## 🖥️ Setup del frontend

### 1. Instalar dependencias
```bash
cd frontend
npm install
```

### 2. Levantar el servidor de desarrollo
```bash
npm run dev
```

✅ Disponible en http://localhost:5173  
✅ Las llamadas a `/api` se redirigen automáticamente al backend (configurado en `vite.config.js`)

---

## 📁 Estructura del proyecto
```
proyecto-demo/
├── backend/
│   ├── app.py          ← Rutas y configuración de Flask
│   ├── models.py       ← Modelos SQLAlchemy (User, Note)
│   ├── seed.py         ← Script para datos de prueba
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── App.vue             ← Componente raíz + navbar
    │   ├── main.js             ← Entry point
    │   ├── router/
    │   │   └── index.js        ← Rutas + guards de autenticación
    │   ├── services/
    │   │   ├── api.js          ← Axios + funciones de API
    │   │   └── authStore.js    ← Estado global de autenticación
    │   └── views/
    │       ├── LoginView.vue
    │       ├── RegisterView.vue
    │       └── DashboardView.vue
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
| GET    | /api/notes       | ✅   | Listar notas del usuario |
| POST   | /api/notes       | ✅   | Crear nota               |
| DELETE | /api/notes/:id   | ✅   | Eliminar nota            |

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

# Crear una nota
curl -X POST http://localhost:5000/api/notes \
  -H "Content-Type: application/json" \
  -d '{"title":"Mi nota","content":"Hola mundo"}' \
  -b cookies.txt -c cookies.txt
```