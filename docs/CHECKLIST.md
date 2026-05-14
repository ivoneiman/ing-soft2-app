# ✅ CHECKLIST - Mantener Setup Estandarizado

Antes de commitear cambios, verifica estos puntos para que el setup siga siendo reproducible.

---

## 🔍 Pre-Commit Checklist

- [ ] **Base de datos se crea correctamente**
  ```bash
  rm backend/app.db
  python backend/seed.py
  ```
  Debe mostrar: `✅ SEED COMPLETADO EXITOSAMENTE`

- [ ] **Backend levanta sin errores**
  ```bash
  cd backend
  python app.py
  ```
  Debe mostrar: `Running on http://localhost:5000`

- [ ] **Frontend levanta sin errores**
  ```bash
  cd frontend
  npm run dev
  ```
  Debe mostrar: `Local: http://localhost:5173`

- [ ] **Login funciona con datos de prueba**
  - Abre http://localhost:5173
  - Login con `admin@test.com` / `admin123`
  - Debe mostrar dashboard

- [ ] **No hay errores en consola/terminal**
  - Backend: sin errores Python
  - Frontend: sin errores JavaScript/Vue

---

## 📝 Si Agregas/Cambias Dependencias

### Backend (Python)

```bash
# 1. Instala la nueva dependencia
pip install nombre-del-paquete

# 2. Guarda en requirements.txt
pip freeze > requirements.txt

# 3. Verifica que seed.py siga funcionando
python backend/seed.py

# 4. Verifica que app.py levante
python app.py
```

**Commit message:** `chore: add [package] to backend dependencies`

### Frontend (JavaScript)

```bash
# 1. Instala el nuevo paquete
npm install nombre-del-paquete

# 2. Verifica que todo funciona
npm run dev

# 3. Abre http://localhost:5173 y prueba
```

**Commit message:** `chore: add [package] to frontend dependencies`

---

## 🗄️ Si Cambias la Base de Datos

### Agregar un modelo nuevo

1. **Edita `backend/models.py`**
   - Define la clase modelo
   - Agrega relaciones necesarias

2. **Actualiza `backend/seed.py`**
   - Agrega datos de prueba para el nuevo modelo
   - Valida existencia antes de crear

3. **Verifica**
   ```bash
   rm backend/app.db
   python backend/seed.py
   ```

4. **Commit message:** `feat: add [modelo] model to database`

### Cambiar columnas existentes

⚠️ **IMPORTANTE:** El equipo usa SQLite en desarrollo, no hay migrations.

- Si cambias/agregas columnas: Asegúrate de actualizar `seed.py`
- Comunica cambios al equipo por Slack/Discord
- Todos deben borrar `app.db` y ejecutar `seed.py` nuevamente

---

## 🎨 Si Cambias Frontend

### Agregar vista nueva

1. **Crea en `frontend/src/views/[nombre]/`**
2. **Agrega ruta en `frontend/src/router/index.js`**
3. **Verifica con `npm run dev`**
4. **Commit message:** `feat: add [feature] view`

### Agregar componente reutilizable

1. **Crea en `frontend/src/components/`**
2. **Exporta desde componentes existentes**
3. **Verifica renderizado**
4. **Commit message:** `feat: add [componente] component`

---

## 🔗 Si Cambias la API

### Agregar endpoint nuevo

1. **Edita `backend/app.py`**
   ```python
   @app.route("/api/nueva-ruta", methods=["POST"])
   def nueva_ruta():
       # ... lógica
       return jsonify({...}), 200
   ```

2. **Actualiza `frontend/src/services/api.js`**
   ```javascript
   export async function llamarNuevaRuta(datos) {
       return axios.post("/api/nueva-ruta", datos);
   }
   ```

3. **Verifica en frontend que funcione**
4. **Commit message:** `feat: add [endpoint] API endpoint`

### Cambiar estructura de respuesta

- Actualiza tanto backend como frontend
- Verifica que frontend pueda procesar la nueva respuesta
- **IMPORTANTE:** Comunica cambios antes de commitear

---

## 📚 Documentación

### Si agregas una feature importante:

- [ ] Actualizar `README.md` sección "Flujo de Funcionalidades"
- [ ] Agregar paso en `SETUP_STEP_BY_STEP.md` si aplica
- [ ] Comentar código complicado

### Si haces cambios de arquitectura:

- Crear archivo nuevo en `docs/` explicando
- Actualizar `README.md` si aplica
- Comunicar al equipo

---

## 🧪 Testing Antes de Commit

Ejecuta este script de validación:

```bash
python validate_setup.py
```

Debe mostrar todos los checks en verde ✓

---

## 🚨 Reglas de Oro

### SÍ

- ✅ Mantener seed.py idempotente (puede ejecutarse varias veces)
- ✅ Validar existencia antes de crear datos
- ✅ Agregar logs descriptivos
- ✅ Actualizar .env.example si agregas variables
- ✅ Probar en desarrollo local antes de commitear

### NO

- ❌ Commitear cambios en `app.db` (es generada)
- ❌ Commitear carpetas `node_modules/` o `venv/`
- ❌ Pushear credenciales reales en `.env`
- ❌ Cambiar estructura sin avisar al equipo
- ❌ Romper el setup existente

---

## 🆘 Emergencia: "Rompí algo"

Si accidentalmente rompiste el setup:

1. **NO commitees aún**
2. **Restaura archivo:** `git checkout archivo-problemático`
3. **Prueba setup nuevamente:** `python backend/seed.py`
4. **Repite los cambios más cuidadosamente**
5. **Commit correctamente**

---

## 📞 Dudas

- Revisar README.md
- Revisar SETUP_STEP_BY_STEP.md
- Preguntar en el canal de Discord/Slack del equipo
- Ejecutar `python validate_setup.py` para diagnosticar

---

**Última actualización:** Mayo 2024
