from django.apps import AppConfig


class SharedConfig(AppConfig):
    name = "shared"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from . import signals  # noqa: F401
