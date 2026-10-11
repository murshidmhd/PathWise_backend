import firebase_admin
from firebase_admin import credentials
from django.conf import settings

from django.apps import AppConfig
import os


class YourAppConfig(AppConfig):
    name = 'notifications'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        # Initialize Firebase Admin SDK only if not already initialized
        if not firebase_admin._apps:
            cred = credentials.Certificate(settings.FIREBASE_ACCOUNT_KEY_PATH)
            firebase_admin.initialize_app(cred)