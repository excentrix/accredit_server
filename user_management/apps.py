from django.apps import AppConfig
from django.apps import AppConfig
from django.db.models.signals import post_migrate


class UserManagementConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "user_management"

    def ready(self):
        from .signals import create_permissions
        post_migrate.connect(create_permissions, sender=self)