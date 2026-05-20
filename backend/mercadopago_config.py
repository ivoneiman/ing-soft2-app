import os

import mercadopago
from dotenv import load_dotenv


load_dotenv()


def get_mercadopago_client():
    access_token = os.getenv("MERCADOPAGO_ACCESS_TOKEN")
    if not access_token:
        raise RuntimeError("MERCADOPAGO_ACCESS_TOKEN no está configurado")

    return mercadopago.SDK(access_token)
