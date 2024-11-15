from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Department, AcademicYear, Template
from datetime import date

User = get_user_model()

class Command(BaseCommand):
    help = 'Sets up initial data including departments, templates, and users'

    def handle(self, *args, **kwargs):
        # Create departments
        departments_data = [
            {'name': 'Computer Science and Engineering', 'code': 'CSE'},
            {'name': 'Electronics and Communication', 'code': 'ECE'},
            {'name': 'Mechanical Engineering', 'code': 'ME'},
        ]
        
        departments = []
        for dept_data in departments_data:
            dept, created = Department.objects.get_or_create(
                code=dept_data['code'],
                defaults={'name': dept_data['name']}
            )
            departments.append(dept)
            action = 'Created' if created else 'Already exists'
            self.stdout.write(self.style.SUCCESS(f'{action}: Department {dept.name}'))

        # Create academic years
        academic_years_data = [
            {
                'year': '2023-24',
                'start_date': date(2023, 6, 1),
                'end_date': date(2024, 5, 31),
                'is_current': True
            },
            {
                'year': '2022-23',
                'start_date': date(2022, 6, 1),
                'end_date': date(2023, 5, 31),
                'is_current': False
            },
        ]

        for year_data in academic_years_data:
            academic_year, created = AcademicYear.objects.get_or_create(
                year=year_data['year'],
                defaults={
                    'start_date': year_data['start_date'],
                    'end_date': year_data['end_date'],
                    'is_current': year_data['is_current']
                }
            )
            action = 'Created' if created else 'Already exists'
            self.stdout.write(self.style.SUCCESS(f'{action}: Academic Year {academic_year.year}'))

        # Create templates
        templates_data = [
            {
                'code': '1.1.1',
                'name': 'Number of Programs',
                'description': 'Number of programs offered year-wise during the last five years',
                'headers': ['Program Name', 'Program Code', 'Year', 'Number of Students', 'Status'],
                'columns': [
                    {
                        'name': 'program_name',
                        'display_name': 'Program Name',
                        'type': 'string',
                        'required': True,
                        'description': 'Name of the program'
                    },
                    {
                        'name': 'program_code',
                        'display_name': 'Program Code',
                        'type': 'string',
                        'required': True,
                        'description': 'Unique code for the program'
                    },
                    {
                        'name': 'year',
                        'display_name': 'Year',
                        'type': 'string',
                        'required': True,
                        'description': 'Academic year'
                    },
                    {
                        'name': 'number_of_students',
                        'display_name': 'Number of Students',
                        'type': 'number',
                        'required': True,
                        'description': 'Total number of students enrolled'
                    },
                    {
                        'name': 'status',
                        'display_name': 'Status',
                        'type': 'select',
                        'required': True,
                        'description': 'Current status of the program',
                        'options': ['Active', 'Inactive', 'Discontinued']
                    }
                ]
            },
            {
                'code': '1.2.1',
                'name': 'New Courses Introduced',
                'description': 'New courses introduced across programs during the last five years',
                'headers': ['Course Name', 'Course Code', 'Program', 'Introduction Year', 'Credits'],
                'columns': [
                    {
                        'name': 'course_name',
                        'display_name': 'Course Name',
                        'type': 'string',
                        'required': True,
                        'description': 'Name of the course'
                    },
                    {
                        'name': 'course_code',
                        'display_name': 'Course Code',
                        'type': 'string',
                        'required': True,
                        'description': 'Unique code for the course'
                    },
                    {
                        'name': 'program',
                        'display_name': 'Program',
                        'type': 'string',
                        'required': True,
                        'description': 'Program offering the course'
                    },
                    {
                        'name': 'introduction_year',
                        'display_name': 'Introduction Year',
                        'type': 'string',
                        'required': True,
                        'description': 'Year when the course was introduced'
                    },
                    {
                        'name': 'credits',
                        'display_name': 'Credits',
                        'type': 'number',
                        'required': True,
                        'description': 'Number of credits for the course'
                    }
                ]
            },
            {
                'code': '2.1.1',
                'name': 'Student Enrollment',
                'description': 'Year-wise enrollment of students during the last five years',
                'headers': ['Category', 'Gender', 'Year', 'Number of Students'],
                'columns': [
                    {
                        'name': 'category',
                        'display_name': 'Category',
                        'type': 'select',
                        'required': True,
                        'description': 'Student category',
                        'options': ['SC', 'ST', 'OBC', 'General', 'Others']
                    },
                    {
                        'name': 'gender',
                        'display_name': 'Gender',
                        'type': 'select',
                        'required': True,
                        'description': 'Gender of students',
                        'options': ['Male', 'Female', 'Other']
                    },
                    {
                        'name': 'year',
                        'display_name': 'Year',
                        'type': 'string',
                        'required': True,
                        'description': 'Academic year'
                    },
                    {
                        'name': 'number_of_students',
                        'display_name': 'Number of Students',
                        'type': 'number',
                        'required': True,
                        'description': 'Total number of students'
                    }
                ]
            }
        ]

        for template_data in templates_data:
            template, created = Template.objects.get_or_create(
                code=template_data['code'],
                defaults={
                    'name': template_data['name'],
                    'description': template_data['description'],
                    'headers': template_data['headers'],
                    'columns': template_data['columns']
                }
            )
            action = 'Created' if created else 'Already exists'
            self.stdout.write(self.style.SUCCESS(f'{action}: Template {template.code}'))

        # Create users
        # Admin user
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(f'Created admin user: {admin_user.username}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Admin user already exists: {admin_user.username}'))

        # IQAC director
        iqac_director, created = User.objects.get_or_create(
            username='iqac',
            defaults={
                'email': 'iqac@example.com',
                'role': 'iqac_director'
            }
        )
        if created:
            iqac_director.set_password('iqac123')
            iqac_director.save()
            self.stdout.write(self.style.SUCCESS(f'Created IQAC director: {iqac_director.username}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'IQAC director already exists: {iqac_director.username}'))

        # Faculty users for each department
        for dept in departments:
            username = f'faculty_{dept.code.lower()}'
            faculty, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.com',
                    'role': 'faculty',
                    'department': dept
                }
            )
            if created:
                faculty.set_password('faculty123')
                faculty.save()
                self.stdout.write(self.style.SUCCESS(f'Created faculty user for {dept.name}: {faculty.username}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Faculty user already exists for {dept.name}: {faculty.username}'))