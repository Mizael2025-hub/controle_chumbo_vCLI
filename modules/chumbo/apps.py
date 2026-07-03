from django.apps import AppConfig


class ChumboConfig(AppConfig):
    name = "modules.chumbo"
    label = "chumbo"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from modules.chumbo.manifest import MANIFEST
        from modules.registry import register

        register(MANIFEST)
