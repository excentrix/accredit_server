from django.core.management.base import BaseCommand
from api.models import Department

class Command(BaseCommand):
    help = 'Populate the Department database with predefined departments'

    def handle(self, *args, **options):
        departments = [
                    {'id': 0, 'name': 'Admin'},
                    {'id': 1, 'name': 'Artificial Intelligence and Data Science'},
                    {'id': 2, 'name': 'Artificial Intelligence and Machine learning'},
                    {'id': 3, 'name': 'Computer Science and Engineering'},
                    {'id': 4, 'name': 'Information Science and Engineering'},
                    {'id': 5, 'name': 'Electronics and Communication Engineering'},
                    {'id': 6, 'name': 'Electrical and Electronics Engineering'},
                    {'id': 7, 'name': 'Aeronautical Engineering'},
                    {'id': 8, 'name': 'Mechanical Engineering'},
                    {'id': 9, 'name': 'Civil Engineering'},
                    {'id': 10, 'name': 'Computer Science & Engg. ( AI & ML)'},
                ]


        for dept_data in departments:
            department = Department(**dept_data)
            department.save()

        self.stdout.write(self.style.SUCCESS('Departments successfully populated'))
