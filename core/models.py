# core/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.dateparse import parse_date
from django.core.exceptions import ValidationError
from django.core.validators import validate_email, URLValidator
# from django.contrib.postgres.fields import JSONField

class User(AbstractUser):
    ROLE_CHOICES = [
        ('faculty', 'Faculty'),
        ('iqac_director', 'IQAC Director'),
        ('admin', 'Admin'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    department = models.ForeignKey(
        'Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )

    class Meta:
        ordering = ['username']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    
    def __str__(self):
        return self.name

class AcademicYear(models.Model):
    name = models.CharField(max_length=9)  # e.g., "2023-2024"
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    transition_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed')
        ],
        default='pending'
    )
    transition_completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_current:
            AcademicYear.objects.exclude(id=self.id).update(is_current=False)
        super().save(*args, **kwargs)

class AcademicYearTransition(models.Model):
    from_year = models.ForeignKey(
        AcademicYear, 
        on_delete=models.PROTECT,
        related_name='transitions_from'
    )
    to_year = models.ForeignKey(
        AcademicYear, 
        on_delete=models.PROTECT,
        related_name='transitions_to'
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('failed', 'Failed')
        ],
        default='pending'
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_log = models.TextField(null=True, blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.PROTECT)

    class Meta:
        ordering = ['-started_at']
        unique_together = ['from_year', 'to_year']
        
        
class Template(models.Model):
    """Stores the structure of different NAAC document templates"""
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=500)
    # description = models.TextField(null=True, blank=True)
    # headers = models.JSONField()
    metadata = models.JSONField()
    # columns = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # column_groups = models.JSONField(default=list)
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    
    # class Meta:
    #     ordering = ['code']

class DataSubmission(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    )

    template = models.ForeignKey('Template', on_delete=models.PROTECT)
    department = models.ForeignKey('Department', on_delete=models.PROTECT)
    academic_year = models.ForeignKey('AcademicYear', on_delete=models.PROTECT)
    submitted_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='submissions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    submitted_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True, 
        related_name='verified_submissions'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['template', 'department', 'academic_year']
        ordering = ['-academic_year__start_date', '-updated_at']


    def __str__(self):
        return f"{self.template.code} - {self.department.name} ({self.academic_year})"

    def clean(self):
        # Ensure only IQAC directors can verify submissions
        if self.verified_by and self.verified_by.role != 'iqac_director':
            raise ValidationError("Only IQAC directors can verify submissions")
        
        # Ensure submission can only be verified if it's in submitted state
        if self.verified_by and self.status == 'draft':
            raise ValidationError("Cannot verify a draft submission")

class SubmissionData(models.Model):
    submission = models.ForeignKey(
        DataSubmission, 
        on_delete=models.CASCADE, 
        related_name='data_rows'
    )
    section_index = models.IntegerField()
    row_number = models.IntegerField()
    data = models.JSONField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['section_index', 'row_number']
        unique_together = ['submission', 'section_index', 'row_number']

    def clean(self):
        if self.section_index >= len(self.submission.template.metadata):
            raise ValidationError("Invalid section index")
        
        # Validate data against template structure
        self.validate_data_against_template()

    def validate_data_against_template(self):
        """Validate the data against the template structure"""
        section = self.submission.template.metadata[self.section_index]
        template_columns = self._flatten_columns(section['columns'])
        
        # Check required fields
        for column in template_columns:
            if column['required'] and not self.data.get(column['name']):
                raise ValidationError(f"Required field missing: {column['name']}")
            
            # Validate data type
            if value := self.data.get(column['name']):
                self._validate_field_value(value, column)

    def _flatten_columns(self, columns, prefix=''):
        """Flatten nested columns structure"""
        flat_columns = []
        for column in columns:
            if column['type'] == 'single':
                name = f"{prefix}{column['name']}" if prefix else column['name']
                flat_columns.append({**column, 'name': name})
            elif column['type'] == 'group':
                group_prefix = f"{prefix}{column['name']}_" if prefix else f"{column['name']}_"
                flat_columns.extend(self._flatten_columns(column['columns'], group_prefix))
        return flat_columns

    def _validate_field_value(self, value, column):
        """Validate a single field value against its column definition"""
        try:
            if column['data_type'] == 'number':
                float(value)
            elif column['data_type'] == 'date':
                parse_date(value)
            elif column['data_type'] == 'email':
                validate_email(value)
            elif column['data_type'] == 'url':
                URLValidator()(value)
            elif column['data_type'] == 'option':
                if value not in column['options']:
                    raise ValidationError(f"Invalid option for {column['name']}: {value}")
        except (ValueError, ValidationError) as e:
            raise ValidationError(f"Invalid {column['data_type']} for {column['name']}: {value}")