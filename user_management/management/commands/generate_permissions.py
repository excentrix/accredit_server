# user_management/management/commands/generate_permissions.py
from django.apps import apps
from django.core.management.base import BaseCommand
from user_management.models import Module, Permission

class Command(BaseCommand):
    help = 'Generate permissions dynamically for all installed apps.'

    def handle(self, *args, **kwargs):
        actions = {
            'view': 'Can view {}',
            'create': 'Can create new {}',
            'update': 'Can update existing {}',
            'delete': 'Can delete {}'
        }

        self.stdout.write(self.style.SUCCESS('Starting permission generation...'))

        for app_config in apps.get_app_configs():
            app_label = app_config.label
            if app_label in ['admin', 'contenttypes', 'sessions', 'messages']:
                continue  # Skip built-in apps
                
            models = app_config.get_models()
            
            # Create or get the module
            module, created = Module.objects.get_or_create(
                name=app_label,
                defaults={'description': f'Permissions for {app_label} module'}
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created module: {app_label}'))

            for model in models:
                model_name = model._meta.model_name
                verbose_name = model._meta.verbose_name.title()

                for action, description_template in actions.items():
                    codename = f"{app_label}:{model_name}:{action}"
                    description = description_template.format(verbose_name)

                    permission, created = Permission.objects.get_or_create(
                        module=module,
                        resource=model_name,
                        action=action,
                        defaults={
                            'codename': codename,
                            'description': description
                        }
                    )

                    if created:
                        self.stdout.write(
                            self.style.SUCCESS(f"Created permission: {codename}")
                        )

        self.stdout.write(self.style.SUCCESS('Permission generation completed!'))