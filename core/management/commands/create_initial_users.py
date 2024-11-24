# core/management/commands/create_initial_users.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Department

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates initial users for testing'

    def handle(self, *args, **kwargs):
        # Create departments
        cs_dept = Department.objects.create(name='Computer Science and Engineering', code='CSE')
        ec_dept = Department.objects.create(name='Electronics and Communications Engineering', code='ECE')

        # Create admin user
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            role='admin',
            is_staff=True,
            is_superuser=True
        )
        self.stdout.write(self.style.SUCCESS(f'Created admin user: {admin_user.username}'))

        # Create IQAC director
        iqac_director = User.objects.create_user(
            username='iqac',
            email='iqac@example.com',
            password='iqac123',
            role='iqac_director'
        )
        self.stdout.write(self.style.SUCCESS(f'Created IQAC director: {iqac_director.username}'))

        # Create faculty users
        faculty1 = User.objects.create_user(
            username='faculty_cs',
            email='faculty_cs@example.com',
            password='faculty123',
            role='faculty',
            department=cs_dept
        )
        self.stdout.write(self.style.SUCCESS(f'Created faculty user: {faculty1.username}'))

        faculty2 = User.objects.create_user(
            username='faculty_ec',
            email='faculty_ec@example.com',
            password='faculty123',
            role='faculty',
            department=ec_dept
        )
        self.stdout.write(self.style.SUCCESS(f'Created faculty user: {faculty2.username}'))