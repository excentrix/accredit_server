# user_management/management/commands/setup_roles.py
from django.core.management.base import BaseCommand
from user_management.models import Role, Permission

class Command(BaseCommand):
    help = 'Create default roles and assign permissions'

    def handle(self, *args, **kwargs):
        # Define roles and their descriptions
        roles = {
            'admin': 'System Administrator with full access',
            'iqac_director': 'IQAC Director with oversight permissions',
            'department_head': 'Department Head with department-level access',
            'faculty': 'Faculty member with basic access',
            'staff': 'Staff member with limited access'
        }

        self.stdout.write(self.style.SUCCESS('Creating roles...'))

        for role_name, description in roles.items():
            role, created = Role.objects.get_or_create(
                name=role_name,
                defaults={'description': description}
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"Created role: {role_name}")
                )

            # Assign permissions based on role
            if role_name == 'admin':
                # Admin gets all permissions
                role.permissions.set(Permission.objects.all())
            elif role_name == 'iqac_director':
                # IQAC Director gets specific permissions
                role.permissions.set(
                    Permission.objects.filter(
                        resource__in=['template', 'submission', 'criterion']
                    )
                )
            # Add more role-specific permission assignments

        self.stdout.write(self.style.SUCCESS('Role setup completed!'))