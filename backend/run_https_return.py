"""
Listener HTTPS local dedicado a los return de Mercado Pago (PAYMENT_SUCCESS_URL,
PAYMENT_FAILURE_URL, PAYMENT_PENDING_URL). Mercado Pago solo activa auto_return
(la redirección automática al volver del checkout) si esas URLs son HTTPS.

Sirve la misma app Flask que backend/app.py, en otro puerto, con un certificado
autofirmado (ad-hoc). El resto de la app (login, API del frontend, etc.) sigue
funcionando por HTTP en el puerto de siempre (backend/app.py, puerto 5000);
esto NO reemplaza a ese proceso, lo complementa.

Uso: correr en paralelo a `python app.py`:
    python run_https_return.py

La primera vez que el navegador entra a esta URL en la sesión (justo al volver
del pago), Chrome va a mostrar "Tu conexión no es privada" por ser un
certificado autofirmado -> hay que click en "Avanzado" > "Continuar a
localhost (no seguro)". Después de eso, en esa misma sesión de navegador no
debería volver a pedirlo.
"""
import os

from app import app

if __name__ == "__main__":
    port = int(os.getenv("HTTPS_RETURN_PORT", 5443))
    app.run(host="0.0.0.0", port=port, ssl_context="adhoc", debug=False)
