from django.apps import apps
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from user_management.models import Module, Permission

@receiver(post_migrate)
def create_permissions(sender, **kwargs):
    actions = ['view', 'create', 'update', 'delete']

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

                if not Permission.objects.filter(codename=codename).exists():
                    Permission.objects.create(
                        module=module,
                        resource=model_name,
                        action=action,
                        codename=codename
                    )
