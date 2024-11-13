# core/models/template.py
from django.db import models
from core.models.mixins import TimeStampedModel
from core.constants import TemplateType, ApprovalStatus

class Template(TimeStampedModel):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file_code = models.CharField(max_length=50, unique=True)
    type = models.CharField(
        max_length=20,
        choices=TemplateType.choices
    )
    columns = models.JSONField(default=list)  # List of column names
    is_active = models.BooleanField(default=True)
    deadline = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['file_code']

    def __str__(self):
        return f"{self.file_code} - {self.title}"

class TemplateData(TimeStampedModel):
    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    department = models.ForeignKey(
        'core.Department',
        on_delete=models.CASCADE,
        related_name='template_submissions'
    )
    academic_year = models.ForeignKey(
        'core.AcademicYear',
        on_delete=models.CASCADE,
        related_name='template_submissions'
    )
    data = models.JSONField()  # Actual template data
    status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.DRAFT
    )
    submitted_by = models.ForeignKey(
        'core.User',
        on_delete=models.CASCADE,
        related_name='template_submissions'
    )
    reviewed_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_submissions'
    )
    review_comments = models.TextField(blank=True)
    review_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['template', 'department', 'academic_year']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.template.file_code} - {self.department.name} ({self.academic_year})"