from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import AcademicYearTransition, Template, DataSubmission, SubmissionData  # Add this import
from django.db.models import Count, Q
from datetime import timedelta
from django.db.models.functions import TruncDate
from user_management.models import Department
class AcademicYearTransitionService:
    def __init__(self, from_year, to_year, user):
        self.from_year = from_year
        self.to_year = to_year
        self.user = user
        self.transition = None

    @transaction.atomic
    def start_transition(self):
        """Initialize the transition process"""
        if self.from_year.transition_status != 'completed':
            raise ValidationError("Previous academic year is not properly closed")

        if AcademicYearTransition.objects.filter(
            to_year=self.to_year,
            status__in=['pending', 'in_progress']
        ).exists():
            raise ValidationError("A transition to this academic year is already in progress")

        self.transition = AcademicYearTransition.objects.create(
            from_year=self.from_year,
            to_year=self.to_year,
            status='in_progress',
            processed_by=self.user
        )

        self.to_year.transition_status = 'in_progress'
        self.to_year.save()

        return self.transition

    def process_transition(self):
        """Process the actual transition"""
        try:
            # 1. Create new submissions for continuous templates
            self._create_continuous_submissions()
            
            # 2. Carry forward relevant data
            self._carry_forward_data()
            
            # 3. Mark transition as completed
            self._complete_transition()

        except Exception as e:
            self._handle_transition_error(str(e))
            raise

    def _create_continuous_submissions(self):
        """Create new submissions for templates that need yearly continuation"""
        continuous_templates = Template.objects.filter(
            metadata__contains={'continuous': True}
        )

        for template in continuous_templates:
            # Get all departments that had submissions in previous year
            previous_submissions = DataSubmission.objects.filter(
                template=template,
                academic_year=self.from_year,
                status='approved'
            )

            for prev_submission in previous_submissions:
                # Create new submission for the new academic year
                DataSubmission.objects.create(
                    template=template,
                    department=prev_submission.department,
                    academic_year=self.to_year,
                    submitted_by=self.user,
                    status='draft'
                )

    def _carry_forward_data(self):
        """Carry forward data that needs to be preserved"""
        carry_forward_templates = Template.objects.filter(
            metadata__contains={'carry_forward': True}
        )

        for template in carry_forward_templates:
            previous_submissions = DataSubmission.objects.filter(
                template=template,
                academic_year=self.from_year,
                status='approved'
            ).prefetch_related('data_rows')

            for prev_submission in previous_submissions:
                new_submission = DataSubmission.objects.create(
                    template=template,
                    department=prev_submission.department,
                    academic_year=self.to_year,
                    submitted_by=self.user,
                    status='draft'
                )

                # Copy eligible data rows
                for data_row in prev_submission.data_rows.all():
                    if self._should_carry_forward(data_row, template):
                        SubmissionData.objects.create(
                            submission=new_submission,
                            section_index=data_row.section_index,
                            row_number=data_row.row_number,
                            data=self._process_carried_data(data_row.data, template)
                        )

    def _should_carry_forward(self, data_row, template):
        """Determine if a data row should be carried forward"""
        # Implementation depends on your specific rules
        carry_forward_rules = template.metadata.get('carry_forward_rules', {})
        return True  # Implement your specific logic

    def _process_carried_data(self, data, template):
        """Process data being carried forward"""
        # Implementation depends on your specific rules
        processed_data = data.copy()
        # Add any necessary transformations
        return processed_data

    @transaction.atomic
    def _complete_transition(self):
        """Mark the transition as completed"""
        self.transition.status = 'completed'
        self.transition.completed_at = timezone.now()
        self.transition.save()

        self.to_year.transition_status = 'completed'
        self.to_year.is_current = True
        self.to_year.save()

    def _handle_transition_error(self, error_message):
        """Handle any errors during transition"""
        if self.transition:
            self.transition.status = 'failed'
            self.transition.error_log = error_message
            self.transition.save()

        self.to_year.transition_status = 'pending'
        self.to_year.save()
        
        
class DashboardService:
    @staticmethod
    def get_overall_stats(academic_year_id, board_id):
        submissions = DataSubmission.objects.filter(
            academic_year_id=academic_year_id,
            template__criteria__board_id=board_id
        )

        total_submissions = submissions.count()
        pending_review = submissions.filter(status='submitted').count()
        approved_submissions = submissions.filter(status='approved').count()
        rejected_submissions = submissions.filter(status='rejected').count()

        # Calculate completion rate
        total_required = Template.objects.filter(
            criteria__board_id=board_id
        ).count() * Department.objects.count()
        
        completion_rate = (approved_submissions / total_required * 100) if total_required > 0 else 0

        return {
            'total_submissions': total_submissions,
            'pending_review': pending_review,
            'approved_submissions': approved_submissions,
            'rejected_submissions': rejected_submissions,
            'completion_rate': round(completion_rate, 2),
        }

    @staticmethod
    def get_activity_timeline(academic_year_id, board_id, days=30, department_id=None):
        start_date = timezone.now() - timedelta(days=days)
        
        queryset = DataSubmission.objects.filter(
            academic_year_id=academic_year_id,
            template__criteria__board_id=board_id,
            updated_at__gte=start_date
        )

        if department_id:
            queryset = queryset.filter(department_id=department_id)

        return queryset.annotate(
            date=TruncDate('updated_at')
        ).values('date').annotate(
            submissions=Count('id', filter=Q(status='submitted')),
            approvals=Count('id', filter=Q(status='approved')),
            rejections=Count('id', filter=Q(status='rejected'))
        ).order_by('date')

    @staticmethod
    def get_criteria_completion(academic_year_id, board_id):
        from django.db.models import F
        return DataSubmission.objects.filter(
            academic_year_id=academic_year_id,
            template__criteria__board_id=board_id,
            status='approved'
        ).values(
            criterion_number=F('template__criteria__number'),
            criterion_name=F('template__criteria__name')
        ).annotate(
            completed=Count('id'),
            total=Count('template__criteria__templates')
        ).order_by('criterion_number')

    @staticmethod
    def get_faculty_stats(academic_year_id, board_id, department_id):
        submissions = DataSubmission.objects.filter(
            academic_year_id=academic_year_id,
            template__criteria__board_id=board_id,
            department_id=department_id
        )

        total_templates = Template.objects.filter(
            criteria__board_id=board_id
        ).count()

        return {
            'total_submissions': submissions.count(),
            'pending_templates': total_templates - submissions.count(),
            'approved_submissions': submissions.filter(status='approved').count(),
            'rejected_submissions': submissions.filter(status='rejected').count(),
            'department_progress': round(
                (submissions.filter(status='approved').count() / total_templates * 100) 
                if total_templates > 0 else 0, 
                2
            )
        }