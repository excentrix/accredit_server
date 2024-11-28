from django.apps import apps
from django.core.management.base import BaseCommand
from user_management.models import Module, Permission

class Command(BaseCommand):
    help = 'Generate permissions dynamically for all installed apps.'

    def handle(self, *args, **kwargs):
        actions = ['view', 'create', 'update', 'delete']

        # Iterate over all installed apps
        for app_config in apps.get_app_configs():
            app_label = app_config.label
            models = app_config.get_models()

            # Create or get the module for each app
            module, created = Module.objects.get_or_create(name=app_label)

            # Iterate over all models within the app
            for model in models:
                model_name = model._meta.model_name

                for action in actions:
                    codename = f"{app_label}:{model_name}:{action}"

                    # Ensure permission does not already exist
                    if not Permission.objects.filter(codename=codename).exists():
                        Permission.objects.create(
                            module=module,
                            resource=model_name,
                            action=action,
                            codename=codename
                        )
                        self.stdout.write(self.style.SUCCESS(f"Created permission: {codename}"))
                    else:
                        self.stdout.write(self.style.NOTICE(f"Permission already exists: {codename}"))
