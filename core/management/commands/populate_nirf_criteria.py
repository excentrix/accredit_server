# core/management/commands/populate_nirf_criteria.py
from django.core.management.base import BaseCommand
from core.models import Criteria, Board

class Command(BaseCommand):
    help = 'Populate the database with NIRF criteria'

    def handle(self, *args, **kwargs):
        # First ensure NIRF board exists
        nirf_board, created = Board.objects.get_or_create(
            code='nirf',
            defaults={'name': 'NIRF'}
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('Created NIRF board')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Using existing NIRF board')
            )

        criteria_data = [
            {
                'number': 1,
                'name': 'Teaching, Learning & Resources (TLR)',
                'description': '''
                Student Strength including Doctoral Students
                Faculty-student ratio with emphasis on permanent faculty
                Combined metric for Faculty with PhD (or equivalent) and Experience
                Financial Resources and their Utilization
                '''.strip(),
                'order': 1
            },
            {
                'number': 2,
                'name': 'Research and Professional Practice (RP)',
                'description': '''
                Combined metric for Publications
                Combined metric for Quality of Publications
                IPR and Patents: Published and Granted
                Footprint of Projects and Professional Practice
                '''.strip(),
                'order': 2
            },
            {
                'number': 3,
                'name': 'Graduation Outcomes (GO)',
                'description': '''
                Metric for University Examinations
                Metric for Number of Ph.D. Students Graduated
                Metric for Placement and Higher Studies
                Median Salary
                '''.strip(),
                'order': 3
            },
            {
                'number': 4,
                'name': 'Outreach and Inclusivity (OI)',
                'description': '''
                Percentage of Students from Other States/Countries
                Percentage of Women Students and Faculty
                Economically and Socially Challenged Students
                Facilities for Physically Challenged Students
                '''.strip(),
                'order': 4
            },
            {
                'number': 5,
                'name': 'Perception (PR)',
                'description': '''
                Peer Perception: Academic Peers and Employers
                Public Perception and Brand Value
                Accreditation and Other Academic Excellence Initiatives
                Research Excellence and Industry Connect
                '''.strip(),
                'order': 5
            }
        ]

        created_count = 0
        updated_count = 0

        for data in criteria_data:
            criteria, created = Criteria.objects.update_or_create(
                board=nirf_board,
                number=data['number'],
                defaults={
                    'name': data['name'],
                    'description': data['description'],
                    'order': data['order']
                }
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully {"created" if created else "updated"} NIRF criterion {criteria.number}'
                )
            )

        summary = f'''
        NIRF Criteria population completed:
        - Created: {created_count}
        - Updated: {updated_count}
        - Total: {created_count + updated_count}
        - Board: {nirf_board.name} ({nirf_board.code})
        '''.strip()

        self.stdout.write(self.style.SUCCESS(summary))