# 📋 POLÍTICA DE SETUP Y BASE DE DATOS - DECISIONES CONSOLIDADAS

**Versión:** 1.0 | **Fecha:** Mayo 2024  
**Audiencia:** Equipo de desarrollo INGE2-APP

---

## 🎯 Decisión de Base de Datos

### ✅ DECISIÓN FINAL: SQLite para Desarrollo Local

**Base de datos elegida:**
- **Desarrollo local (todos):** SQLite (`sqlite:///app.db`)
- **Producción (futuro):** PostgreSQL (configurable desde `.env`)

**Razones:**
1. **SQLite es más simple** para desarrollo local - sin servidor externo
2. **Reproducible** - cada developer tiene su propia BD local
3. **Fácil de resetear** - solo borrar `app.db`
4. **Consistente** - toda la documentación y scripts usan SQLite
5. **Configurable** - se puede cambiar a PostgreSQL desde `.env` sin cambiar código

**Verificación:**
- `app.py` usa: `SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///app.db")`
- `.env` define: `SQLALCHEMY_DATABASE_URI=sqlite:///app.db`
- `requirements.txt` NO incluye drivers PostgreSQL (innecesarios para desarrollo)

---

## 🚀 Setup Estandarizado

### Flujo Definido

```bash
# 1. Clonar repositorio
git clone <repo-url>

# 2. Instalar dependencias Python
pip install -r requirements.txt

# 3. Crear base de datos + datos de prueba (idempotente)
python seed.py

# 4. Instalar dependencias Node.js
npm install

# 5. Levantar aplicación
npm run dev  # Frontend
python app.py  # Backend (otra terminal)
```

### Scripts Automáticos

Disponibles para simplificar:
- `setup.bat` - Windows: 4 pasos automáticos
- `setup.sh` - Linux/Mac: 4 pasos automáticos
- `validate_setup.py` - Validar que todo está bien

### Validación

```bash
# Verificar que setup fue exitoso
python validate_setup.py
```

**Debe mostrar:**
- ✓ Estructura Backend OK
- ✓ Estructura Frontend OK
- ✓ Dependencias Python OK
- ✓ Dependencias Node.js OK
- ✓ Base de datos (app.db) existe
- ✓ Puertos disponibles

---

## 📦 Dependencias

### Python (Backend)

**Requeridas:**
```
Flask==3.0.0                # Web framework
Flask-SQLAlchemy==3.1.1    # ORM (agnóstico de BD)
Flask-Login==0.6.3         # Autenticación
Flask-CORS==4.0.0          # CORS (frontend)
python-dotenv==1.0.0       # Variables de entorno
Werkzeug==3.0.1            # Security
tzdata==2026.2             # Timezone data
```

**NO requeridas (removidas):**
- ~~`psycopg==3.3.4`~~ - Driver PostgreSQL (no necesario para SQLite)
- ~~`psycopg-binary==3.3.4`~~ - Binarios PostgreSQL (no necesario para SQLite)

**Razón:** SQLite está built-in en Python, no necesita drivers externos.

### Node.js (Frontend)

**Requeridas:**
```json
{
  "vue": "^3.5.32",
  "vue-router": "^4.3.3",
  "axios": "^1.7.2",
  "qrcode.vue": "^3.9.1",
  "html5-qrcode": "^2.3.8"
}
```

**Devtools:**
```json
{
  "vite": "^5.3.1",
  "@vitejs/plugin-vue": "^5.0.5",
  "concurrently": "^9.0.0"
}
```

---

## 📄 Configuración (Variables de Entorno)

### `.env` (Archivo de desarrollo local)

```bash
# Autenticación
SECRET_KEY=dev-secret-key

# Base de datos
SQLALCHEMY_DATABASE_URI=sqlite:///app.db

# CORS
CORS_ORIGINS=http://localhost:5173

# Entorno
ENVIRONMENT=development
FLASK_DEBUG=1
FLASK_ENV=development
```

### `.env.example` (Referencia para el equipo)

Contiene:
- ✓ Todas las variables disponibles
- ✓ Valores recomendados para desarrollo
- ✓ Explicaciones claras
- ✓ Alternativas (ej: cambiar a PostgreSQL)

**Importante:** No debe commiterse `.env` (es local de cada developer), pero SÍ `.env.example`

---

## 🗄️ Seed.py - Política Idempotente

### Principios

1. **Valida existencia antes de crear**
   - No duplica usuarios
   - No duplica clases
   - No duplica enrollments

2. **Puede ejecutarse múltiples veces**
   ```bash
   python seed.py  # Crea datos
   python seed.py  # No duplica, omite lo existente
   python seed.py  # Sigue sin duplicar
   ```

3. **Mensajes claros**
   - `✓ Usuario creado` - se creó
   - `⊘ Usuario ya existe` - se omitió

### Datos Creados

**Usuarios:**
- admin@test.com / admin123 (rol: admin)
- employee@test.com / employee123 (rol: employee)
- client@test.com / client123 (rol: client)

**Clases:**
- Ingeniería de Software 2
- Programación Avanzada
- Bases de Datos

**Enrollments:**
- Admin → todas las clases
- Employee → 2 clases
- Client → 1 clase

### Flujo Recomendado

```bash
# Primera vez
python seed.py

# Si algo salió mal, borrar BD y reintentar
rm backend/app.db
python seed.py

# O simplemente ejecutar nuevamente (es idempotente)
python seed.py
```

---

## 🛡️ .gitignore - Política de Archivos

### Archivos que NUNCA se comitean

```
*.db              # BD SQLite (generada por seed.py)
*.sqlite          # Variantes de SQLite
*.sqlite3         # Variantes de SQLite
venv/             # Entorno virtual Python
node_modules/     # Dependencias Node.js
.env              # Credenciales locales (usar .env.example)
__pycache__/      # Cache Python
.DS_Store         # macOS files
```

### Por qué

- `app.db` se regenera ejecutando `seed.py`
- `venv/` y `node_modules/` se regeneran con `pip install` y `npm install`
- `.env` contiene credenciales (cada developer hace su propia copia de `.env.example`)

---

## ✅ Checklist de Consolidación

- [x] Base de datos unificada a SQLite
- [x] Dependencias PostgreSQL removidas de requirements.txt
- [x] Configuración en .env (no hardcodeada)
- [x] app.py es configurable desde .env
- [x] .env.example documentado y claro
- [x] seed.py es idempotente
- [x] Documentación consistente (SQLite en todos lados)
- [x] Scripts setup son simples
- [x] validate_setup.py no es complejo
- [x] .gitignore previene commits de BD
- [x] Sin referencias a PostgreSQL en documentación
- [x] Sin cambios arquitectónicos
- [x] Sin Docker
- [x] Sin CI/CD

---

## 📝 Cambios Realizados (Resumen)

| Archivo | Cambio | Razón |
|---------|--------|-------|
| requirements.txt | Removidas psycopg | No necesarias para SQLite |
| .env | Agregada SQLALCHEMY_DATABASE_URI | Consistencia |
| .env.example | Mejorada documentación | Claridad |
| app.py | Ahora lee DB_URI de .env | Flexibilidad futura |
| .gitignore | Agregados *.db, *.sqlite | Prevenir commits de BD |
| seed.py | Verificado idempotente | Validación |
| README.md | Verificado SQLite | Consistencia |

---

## 🚫 Lo que NO cambió

- ✗ Arquitectura del proyecto
- ✗ Lógica de negocio
- ✗ Rutas API
- ✗ Modelos de datos
- ✗ Frontend code
- ✗ Backend logic (excepto configuración)
- ✗ Docker
- ✗ CI/CD

Solo se **estandarizó y consolidó** el setup.

---

## 🔄 Proceso de Cambio en el Equipo

Si alguien quiere cambiar a PostgreSQL en el futuro:

### Paso 1: Actualizar requirements.txt
```bash
pip install psycopg
echo "psycopg==x.x.x" >> requirements.txt
```

### Paso 2: Actualizar .env
```bash
# Cambiar en backend/.env:
SQLALCHEMY_DATABASE_URI=postgresql://user:password@localhost:5432/dbname
```

### Paso 3: Ejecutar seed.py
```bash
python seed.py  # Lee la BD_URI de .env y usa esa
```

**Nota:** El código NO necesita cambios porque app.py ya es flexible.

---

## 📞 Decisiones para el Futuro

### Si agregan nueva feature
- Ejecutar `python seed.py` nuevamente (es idempotente)
- Debería auto-ignorar datos existentes
- Agregar nuevo dato de prueba si es necesario

### Si descubren un bug en seed.py
- Revisar la lógica de validación
- Asegurar que siga siendo idempotente
- Probar ejecutándolo 2-3 veces

### Si quieren resetear la BD
```bash
# Opción 1: Simple
rm backend/app.db
python seed.py

# Opción 2: Más seguro
cd backend
rm app.db
python seed.py
```

---

## ✨ Beneficios Finales

✅ **Setup claro** - Todos los developers siguen el mismo flujo  
✅ **Reproducible** - Exactamente iguales en todas las máquinas  
✅ **Simple** - Sin complejidades innecesarias  
✅ **Documentado** - Claro por qué cada decisión  
✅ **Flexible** - Se puede cambiar a PostgreSQL sin código  
✅ **Idempotente** - seed.py puede ejecutarse N veces  
✅ **Estable** - Listo para que el equipo lo use  

---

**Este documento debe revisarse si:**
- Se cambiar de BD
- Se agregan nuevas dependencias críticas
- Se modifica el setup process

**Última actualización:** Mayo 2024
