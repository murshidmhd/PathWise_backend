import requests

from django.conf import settings


def is_valid_recaptcha(token):
    if settings.DEBUG:
        return True

    data = {
        "secret": settings.RECAPTCHA_SECRET_KEY,
        "response": token,
    }
    response = requests.post(
        "https://www.google.com/recaptcha/api/1",
        data=data,
        timeout=5,
    )
    return response.json().get("success", False)

