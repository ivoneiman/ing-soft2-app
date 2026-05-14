@echo off
REM Script de Setup Automático para Windows
REM Prepara el proyecto para desarrollo local

echo.
echo ======================================================
echo   SETUP AUTOMATICO - INGE2-APP (Windows)
echo ======================================================
echo.

REM Cambiar a directorio backend
cd backend

echo [1/4] Creando entorno virtual...
if not exist "venv" (
    python -m venv venv
    echo     ✓ Entorno virtual creado
) else (
    echo     ⊘ Entorno virtual ya existe
)

echo.
echo [2/4] Activando entorno virtual...
call venv\Scripts\activate.bat
echo     ✓ Entorno activado

echo.
echo [3/4] Instalando dependencias...
pip install -r requirements.txt --quiet
echo     ✓ Dependencias instaladas

echo.
echo [4/4] Creando base de datos con datos de prueba...
python seed.py
echo.

echo.
echo ======================================================
echo   ✅ SETUP COMPLETADO
echo ======================================================
echo.
echo Próximos pasos:
echo.
echo   OPCIÓN A - Levantar todo automáticamente:
echo   $ npm run dev:all
echo.
echo   OPCIÓN B - Levantar manualmente en 2 terminales:
echo.
echo   Terminal 1 (Backend):
echo   $ cd backend
echo   $ venv\Scripts\activate
echo   $ python app.py
echo.
echo   Terminal 2 (Frontend):
echo   $ cd frontend
echo   $ npm install  (solo la primera vez)
echo   $ npm run dev
echo.
echo Frontend: http://localhost:5173
echo Backend:  http://localhost:5000
echo.
echo Credenciales de prueba:
echo   • admin@test.com / admin123
echo   • employee@test.com / employee123
echo   • client@test.com / client123
echo.
echo ======================================================
echo.

pause
