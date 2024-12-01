# user_management/management/commands/setup_user_management.py
from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Run all setup commands for user management'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting user management setup...'))
        
        setup_commands = [
            'generate_permissions',
            'setup_departments',
            'setup_roles'
        ]

        for command in setup_commands:
            self.stdout.write(
                self.style.SUCCESS(f'\nRunning {command}...')
            )
            call_command(command)

        self.stdout.write(
            self.style.SUCCESS('\nUser management setup completed successfully!')
        )