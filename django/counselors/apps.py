from django.apps import AppConfig


class CounselorsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "counselors"

    def ready(self):
        import counselors.signals
