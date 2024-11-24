# core/management/commands/populate_criteria.py
from django.core.management.base import BaseCommand
from core.models import Criteria, Board

class Command(BaseCommand):
    help = 'Populate the database with NAAC criteria'

    def handle(self, *args, **kwargs):
        # First ensure NAAC board exists
        naac_board, created = Board.objects.get_or_create(
            code='naac',
            defaults={'name': 'NAAC'}
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('Created NAAC board')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Using existing NAAC board')
            )

        criteria_data = [
            {
                'number': 1,
                'name': 'Curricular Aspects',
                'description': '''
                Curriculum Design and Development
                Academic Flexibility
                Curriculum Enrichment
                Feedback System
                '''.strip(),
                'order': 1
            },
            {
                'number': 2,
                'name': 'Teaching-learning and Evaluation',
                'description': '''
                Student Enrollment and Profile
                Catering to Student Diversity
                Teaching-Learning Process
                Teacher Profile and Quality
                Evaluation Process and Reforms
                Student Performance and Learning Outcomes
                Student Satisfaction Survey
                '''.strip(),
                'order': 2
            },
            {
                'number': 3,
                'name': 'Research, Innovations and Extension',
                'description': '''
                Promotion of Research and Facilities
                Resource Mobilization for Research
                Innovation Ecosystem
                Research Publications and Awards
                Consultancy
                Extension Activities
                Collaboration
                '''.strip(),
                'order': 3
            },
            {
                'number': 4,
                'name': 'Infrastructure and Learning Resources',
                'description': '''
                Physical Facilities
                Library as a Learning Resource
                IT Infrastructure
                Campus Infrastructure
                '''.strip(),
                'order': 4
            },
            {
                'number': 5,
                'name': 'Student Support and Progression',
                'description': '''
                Student Support
                Student Progression
                Student Participation and Activities
                Alumni Engagement
                '''.strip(),
                'order': 5
            },
            {
                'number': 6,
                'name': 'Governance, Leadership and Management',
                'description': '''
                Institutional Vision and Leadership
                Strategy Development and Deployment
                Faculty Empowerment Strategies
                Financial Management and Resource Mobilization
                Internal Quality Assurance System
                '''.strip(),
                'order': 6
            },
            {
                'number': 7,
                'name': 'Institutional Values and Best Practices',
                'description': '''
                Institutional Values and Social Responsibilities
                Best Practices
                Institutional Distinctiveness
                '''.strip(),
                'order': 7
            },
        ]

        created_count = 0
        updated_count = 0

        for data in criteria_data:
            criteria, created = Criteria.objects.update_or_create(
                board=naac_board,  # Add board to the lookup
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
                    f'Successfully {"created" if created else "updated"} NAAC criterion {criteria.number}'
                )
            )

        summary = f'''
        NAAC Criteria population completed:
        - Created: {created_count}
        - Updated: {updated_count}
        - Total: {created_count + updated_count}
        - Board: {naac_board.name} ({naac_board.code})
        '''.strip()

        self.stdout.write(self.style.SUCCESS(summary))

    def _format_description(self, description):
        """Format the description text by removing extra whitespace"""
        return '\n'.join(
            line.strip() 
            for line in description.split('\n') 
            if line.strip()
        )