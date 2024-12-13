# core/management/commands/create_initial_users.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from user_management.models import Department

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates initial users for testing'

    def handle(self, *args, **kwargs):
        # Create departments
        cs_dept = Department.objects.filter(code='CSE')
        ec_dept = Department.objects.filter(code='ECE')
        print(cs_dept)

        # Create admin user
        admin_user = User.objects.create_user(
            username='admin',
            usn='0',
            email='admin@test.com',
            password='admin123',
            # roles='admin',
            is_staff=True,
            is_superuser=True
        )

        self.stdout.write(self.style.SUCCESS(f'Created admin user: {admin_user.username}'))

        # Create IQAC director
        iqac_director = User.objects.create_user(
            username='iqac',
            usn='1',
            email='iqac@test.com',
            password='iqac123',
            # roles='iqac_director'
        )

        self.stdout.write(self.style.SUCCESS(f'Created IQAC director: {iqac_director.username}'))

        # Create faculty users
        faculty1 = User.objects.create_user(
            username='faculty_cs',
             usn='2',
            email='faculty_cs@test.com',
            password='faculty123',
            # roles='faculty',
            # department=cs_dept
        )

        self.stdout.write(self.style.SUCCESS(f'Created faculty user: {faculty1.username}'))

        faculty2 = User.objects.create_user(
            username='faculty_ec',
             usn='3',
            email='faculty_ec@test.com',
            password='faculty123',
            # role='faculty',
            # departments=ec_dept
        )

        self.stdout.write(self.style.SUCCESS(f'Created faculty user: {faculty2.username}'))