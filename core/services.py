from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import AcademicYearTransition, Template, DataSubmission, SubmissionData  # Add this import

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