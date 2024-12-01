# user_management/management/commands/setup_departments.py
from django.core.management.base import BaseCommand
from user_management.models import Department

class Command(BaseCommand):
    help = 'Create initial departments'

    def handle(self, *args, **kwargs):
        departments = [
            ('CSE', 'Computer Science and Engineering'),
            ('ISE', 'Information Science and Engineering'),
            ('ECE', 'Electronics and Communication Engineering'),
            ('IQAC', 'Internal Quality Assurance Cell'),
            # Add more departments as needed
        ]

        self.stdout.write(self.style.SUCCESS('Creating departments...'))

        for code, name in departments:
            dept, created = Department.objects.get_or_create(
                code=code,
                defaults={'name': name}
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"Created department: {code}")
                )

        self.stdout.write(self.style.SUCCESS('Department setup completed!'))