# guía para el setup

### Windows

```bash
setup.bat
```

Seguir las instrucciones que aparecerán.

### Linux/Mac

```bash
./setup.sh
```

Seguir las instrucciones que aparecerán.

---

## Credenciales de Prueba

Después de ejecutar setup:

| Email | Contraseña |
|-------|-----------|
| admin@test.com | admin123 |
| employee@test.com | employee123 |
| client@test.com | client123 |

---

## Acceso Local

- **Frontend:** http://localhost:5173
- **Backend:** http://localhost:5000

---

## si falló algo

1. Leer: `SETUP_STEP_BY_STEP.md` → Troubleshooting
2. Ejecutar: `python validate_setup.py` → Te dice qué falta
3. Manden al canal de discord sino

---

## Documentación

| Documento | Propósito |
|-----------|-----------|
| `README.md` | Documentación completa |
| `SETUP_STEP_BY_STEP.md` | Paso a paso + troubleshooting |
| `CHECKLIST.md` | Antes de commitear |
| `POLITICA_SETUP_BD.md` | Decisiones técnicas |
| `VALIDACION_FINAL.md` | Validaciones realizadas |

---

## Comandos Útiles

```bash
# Limpiar base de datos y reinicializar
rm backend/app.db
python backend/seed.py

# Validar que todo esté bien
python validate_setup.py

# Levantar backend (terminal 1)
cd backend
venv\Scripts\activate  # o source venv/bin/activate
python app.py

# Levantar frontend (terminal 2)
cd frontend
npm run dev
```

---

## Base de Datos

**Qué es:** SQLite (archivo local `backend/app.db`)  
**Dónde:** `backend/app.db` (se crea automáticamente)  
**Cómo resetear:** `rm backend/app.db && python backend/seed.py`  
**¿Se commitea?** NO (está en .gitignore)

---

## Checklist Pre-Commit

Antes de hacer push:

- [ ] Ejecuté `python validate_setup.py` ✓
- [ ] Backend levanta sin errores
- [ ] Frontend levanta sin errores
- [ ] Datos de prueba funcionan
- [ ] Leí `CHECKLIST.md` si hice cambios

---

**¿Primera vez en el proyecto?**

1. Lee este documento (5 min)
2. Ejecuta `setup.bat` o `setup.sh` (5 min)
3. Abre http://localhost:5173 y prueba login
4. ¡Listo! Comienza a desarrollar

**¿Problemas?** → `SETUP_STEP_BY_STEP.md`

---

*Actualizado: Mayo 2024*
