# SETUP RÁPIDO - Paso a Paso

Sigan estos pasos en orden

---

## Opción Automática (Windows)

```bash
setup.bat
```

Si esto funciona, **listo**, ir a la sección "Levantar la Aplicación" abajo.

Si no funciona, seguir los pasos manuales abajo.

---

## Opción Automática (Linux/Mac)

```bash
chmod +x setup.sh
./setup.sh
```

Si esto funciona, **listo**, vas a sección "Levantar la Aplicación" abajo.

---

## Opción Manual - Paso a Paso

### 1️⃣ Instalar dependencias Python

```bash
cd backend
python -m venv venv

# Windows:
venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

**Resultado esperado:** Terminal muestra prefijo `(venv)`

---

### 2️⃣ Crear base de datos y datos de prueba

```bash
python seed.py
```

**Resultado esperado:**
```
✅ SEED COMPLETADO EXITOSAMENTE
📊 Estadísticas de la base de datos:
   • Usuarios: 3
   • Clases: 3
   • Enrollments: 6
```

Se debe crear archivo `backend/app.db`

---

### 3️⃣ Instalar dependencias JavaScript (Frontend)

En otra terminal:

```bash
cd frontend
npm install
```

**Resultado esperado:** Se crea carpeta `frontend/node_modules/`

---

## ✅ Levantar la Aplicación

### Opción A: Automático (Recomendado)

En la raíz del proyecto:

```bash
cd frontend
npm run dev:all
```

Abre navegador en: **http://localhost:5173**

---

### Opción B: Manual (2 Terminales)

#### Terminal 1 - Backend

```bash
cd backend
venv\Scripts\activate  # Windows: activate, Linux/Mac: source venv/bin/activate
python app.py
```

Espera a ver: `Running on http://localhost:5000`

#### Terminal 2 - Frontend

```bash
cd frontend
npm run dev
```

Espera a ver: `Local: http://localhost:5173`

---

## Probar Login

Ve a http://localhost:5173 y usa cualquiera de estas cuentas:

| Email | Contraseña | Rol |
|-------|-----------|-----|
| admin@test.com | admin123 | Admin |
| employee@test.com | employee123 | Empleado |
| client@test.com | client123 | Cliente |

---

## Si Algo Sale Mal

### Backend no levanta

```bash
# Verificar que el venv esté activado (debe mostrar "venv" en el prefijo)
# Si no está activado:
cd backend
venv\Scripts\activate  # Windows

# Reinstalar si hay error de módulo:
pip install -r requirements.txt
```

### Frontend no levanta

```bash
# Verificar que Node.js esté instalado:
node --version
npm --version

# Si falta instalar dependencias:
cd frontend
npm install

# Si puerto está ocupado, usar otro:
npm run dev -- --port 5174
```

### Base de datos no se crea

```bash
# Borrar base de datos existente y recrear:
cd backend
del app.db  # Windows: del, Linux/Mac: rm
python seed.py
```

---

## Próximos Pasos

- Revisar funcionalidades en `http://localhost:5173`
- Probar login/logout
- Probar generador de QR
- Revisar estructura en `docs/`

---

**¿Todavía hay problemas?** Revisa el README.md sección Troubleshooting.
