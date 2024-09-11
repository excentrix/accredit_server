# create_groups.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Create custom groups and assign permissions'

    def handle(self, *args, **options):
        # Create a group
        group, created = Group.objects.get_or_create(name='Admin')
        group, created = Group.objects.get_or_create(name='Faculty')
        group, created = Group.objects.get_or_create(name='NH')

        # Assign permissions to the group
        # content_type = ContentType.objects.get_for_model(MyModel)  # Replace with your model
        # permission = Permission.objects.get(content_type=content_type, codename='can_view')
        # group.permissions.add(permission)

        self.stdout.write(self.style.SUCCESS('Successfully created and configured the groups.'))
