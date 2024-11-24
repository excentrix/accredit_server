# core/management/commands/populate_nba_criteria.py
from django.core.management.base import BaseCommand
from core.models import Criteria, Board

class Command(BaseCommand):
    help = 'Populate the database with NBA criteria'

    def handle(self, *args, **kwargs):
        # First ensure NBA board exists
        nba_board, created = Board.objects.get_or_create(
            code='nba',
            defaults={'name': 'NBA'}
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('Created NBA board')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Using existing NBA board')
            )

        criteria_data = [
            {
                'number': 1,
                'name': 'Vision, Mission and Program Educational Objectives',
                'description': '''
                Vision and Mission
                Program Educational Objectives
                Achievement of Program Educational Objectives
                Assessment of Achievement of Program Educational Objectives
                '''.strip(),
                'order': 1
            },
            {
                'number': 2,
                'name': 'Program Curriculum and Teaching-Learning Processes',
                'description': '''
                Program Curriculum
                Teaching-Learning Processes
                Course Outcomes and Program Outcomes
                Assessment of Course Outcomes and Program Outcomes
                '''.strip(),
                'order': 2
            },
            {
                'number': 3,
                'name': 'Course Outcomes and Program Outcomes',
                'description': '''
                Establishment of Course Outcomes
                Attainment of Course Outcomes
                Assessment Tools and Processes
                Evaluation of Attainment
                '''.strip(),
                'order': 3
            },
            {
                'number': 4,
                'name': 'Students\' Performance',
                'description': '''
                Enrollment Ratio
                Success Rate
                Academic Performance
                Placement and Higher Studies
                Professional Activities
                '''.strip(),
                'order': 4
            },
            {
                'number': 5,
                'name': 'Faculty Information and Contributions',
                'description': '''
                Student-Faculty Ratio
                Faculty Qualifications
                Faculty Retention
                Faculty Research Publications
                Faculty Intellectual Property Rights
                Faculty Development
                '''.strip(),
                'order': 5
            },
            {
                'number': 6,
                'name': 'Facilities and Technical Support',
                'description': '''
                Classrooms and Laboratories
                Technical Manpower Support
                Equipment and Experimental Setup
                Laboratory Maintenance and Upgrades
                Safety Measures
                '''.strip(),
                'order': 6
            },
            {
                'number': 7,
                'name': 'Continuous Improvement',
                'description': '''
                Actions taken based on the results of evaluation of Course Outcomes
                Academic Audit and Actions Taken
                Improvement in Success Index of Students
                Improvement in Student Learning
                New Facility Created
                '''.strip(),
                'order': 7
            },
        ]

        created_count = 0
        updated_count = 0

        for data in criteria_data:
            criteria, created = Criteria.objects.update_or_create(
                board=nba_board,
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
                    f'Successfully {"created" if created else "updated"} NBA criterion {criteria.number}'
                )
            )

        summary = f'''
        NBA Criteria population completed:
        - Created: {created_count}
        - Updated: {updated_count}
        - Total: {created_count + updated_count}
        - Board: {nba_board.name} ({nba_board.code})
        '''.strip()

        self.stdout.write(self.style.SUCCESS(summary))