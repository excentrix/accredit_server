# core/models.py
from django.db import models
from django.utils.dateparse import parse_date
from django.core.exceptions import ValidationError
from django.core.validators import validate_email, URLValidator
from user_management.models import CustomUser as User


class Criteria(models.Model):
    board = models.ForeignKey(
        'Board', 
        on_delete=models.PROTECT,
        related_name='criteria'
    )
    number = models.IntegerField()
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    order = models.IntegerField(default=0)
    

    class Meta:
        ordering = ['order', 'number']
        verbose_name_plural = "Criteria"
        unique_together = ['board', 'number']  # Changed from just unique=True on number

    def __str__(self):
        return f"{self.board.name} Criterion {self.number}: {self.name}"

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
        
class Board(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    
    def __str__(self):
        return self.name
        
class Template(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(
        max_length=20,
        help_text="Template code (e.g., '2.1.1')"
    )
    name = models.CharField(
        max_length=500,
        help_text="Template name/title"
    )
    criteria = models.ForeignKey(
    'Criteria',
    on_delete=models.PROTECT,
    related_name='templates',
    )
    metadata = models.JSONField(
        help_text="Template structure including sections, headers, and columns"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    

    class Meta:
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['created_at']),
        ]
        unique_together = ['criteria', 'code']
        
    @property
    def board(self):
        return self.criteria.board if self.criteria else None
    
    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        """Validate the template structure"""
        if not isinstance(self.metadata, list):
            raise ValidationError("Metadata must be a list of sections")

        for section in self.metadata:
            self._validate_section(section)

    def _validate_section(self, section):
        """Validate a single section structure"""
        if not isinstance(section, dict):
            raise ValidationError("Each section must be a dictionary")

        required_keys = {'headers', 'columns'}
        if not all(key in section for key in required_keys):
            raise ValidationError(f"Section missing required keys: {required_keys}")

        if not isinstance(section['headers'], list):
            raise ValidationError("Headers must be a list")

        if not isinstance(section['columns'], list):
            raise ValidationError("Columns must be a list")

        for column in section['columns']:
            self._validate_column(column)

    def _validate_column(self, column, is_nested=False):
        """Validate a column definition"""
        required_keys = {'name', 'type'}
        if not all(key in column for key in required_keys):
            raise ValidationError(f"Column missing required keys: {required_keys}")

        if column['type'] not in ['single', 'group']:
            raise ValidationError(f"Invalid column type: {column['type']}")

        if column['type'] == 'single':
            self._validate_single_column(column)
        elif column['type'] == 'group':
            if 'columns' not in column:
                raise ValidationError("Group column must have nested columns")
            for nested_column in column['columns']:
                self._validate_column(nested_column, is_nested=True)

    def _validate_single_column(self, column):
        """Validate a single column definition"""
        if 'data_type' not in column:
            raise ValidationError("Single column must have data_type")

        valid_data_types = {
            'string', 'number', 'date', 'email', 
            'url', 'option', 'file', 'boolean'
        }
        if column['data_type'] not in valid_data_types:
            raise ValidationError(f"Invalid data_type: {column['data_type']}")

        if column['data_type'] == 'option' and 'options' not in column:
            raise ValidationError("Option type must have options list")

    def get_flat_columns(self):
        """Get flattened list of all columns"""
        flat_columns = []
        for section in self.metadata:
            for column in section['columns']:
                flat_columns.extend(self._flatten_column(column))
        return flat_columns

    def _flatten_column(self, column, prefix=''):
        """Recursively flatten nested columns"""
        flat_columns = []
        current_name = f"{prefix}{column['name']}" if prefix else column['name']

        if column['type'] == 'single':
            flat_columns.append({
                **column,
                'name': current_name
            })
        elif column['type'] == 'group':
            for nested_column in column['columns']:
                flat_columns.extend(
                    self._flatten_column(
                        nested_column, 
                        f"{current_name}_"
                    )
                )
        return flat_columns
    
    def _flatten_column_names(self, columns, prefix=''):
        """Get flattened dictionary of column names and their definitions"""
        flat_columns = {}
        for column in columns:
            current_name = f"{prefix}{column['name']}" if prefix else column['name']
            
            if column['type'] == 'single':
                flat_columns[current_name] = column
            elif column['type'] == 'group':
                flat_columns.update(
                    self._flatten_column_names(
                        column['columns'],
                        f"{current_name}_"
                    )
                )
        return flat_columns

    def validate_data(self, data, section_index):
        """Validate submitted data against template structure"""
        if section_index >= len(self.metadata):
            raise ValidationError("Invalid section index")

        section = self.metadata[section_index]
        flat_columns = self._flatten_column_names(section['columns'])
        
        # Validate required fields and data types
        for column_name, column_def in flat_columns.items():
            if column_def.get('required', False) and column_name not in data:
                raise ValidationError(f"Required field missing: {column_name}")
            
            if column_name in data:
                self._validate_field_value(
                    data[column_name],
                    column_def,
                    column_name
                )

    def _flatten_column_names(self, columns, prefix=''):
        """Get flattened dictionary of column names and their definitions"""
        flat_columns = {}
        for column in columns:
            current_name = f"{prefix}{column['name']}" if prefix else column['name']
            
            if column['type'] == 'single':
                flat_columns[current_name] = column
            elif column['type'] == 'group':
                flat_columns.update(
                    self._flatten_column_names(
                        column['columns'],
                        f"{current_name}_"
                    )
                )
        return flat_columns

    def _validate_field_value(self, value, column_def, column_name):
        """Validate a single field value"""
        if value is None or value == '':
            if column_def.get('required', False):
                raise ValidationError(f"Required field empty: {column_name}")
            return

        data_type = column_def['data_type']
        validation = column_def.get('validation', {})

        try:
            if data_type == 'number':
                self._validate_number(value, validation)
            elif data_type == 'date':
                self._validate_date(value)
            elif data_type == 'email':
                self._validate_email(value)
            elif data_type == 'url':
                self._validate_url(value)
            elif data_type == 'option':
                self._validate_option(value, column_def.get('options', []))
            elif data_type == 'string':
                self._validate_string(value, validation)
        except ValidationError as e:
            raise ValidationError(f"{column_name}: {str(e)}")

    # Add specific validation methods for each data type
    def _validate_number(self, value, validation):
        try:
            num_value = float(value)
            if 'min' in validation and num_value < validation['min']:
                raise ValidationError(f"Value must be >= {validation['min']}")
            if 'max' in validation and num_value > validation['max']:
                raise ValidationError(f"Value must be <= {validation['max']}")
        except (TypeError, ValueError):
            raise ValidationError("Invalid number format")

    def _validate_date(self, value):
        # Add date validation logic
        pass

    def _validate_email(self, value):
        # Add email validation logic
        pass

    def _validate_url(self, value):
        # Add URL validation logic
        pass

    def _validate_option(self, value, options):
        if value not in options:
            raise ValidationError(f"Value must be one of: {', '.join(options)}")

    def _validate_string(self, value, validation):
        if not isinstance(value, str):
            raise ValidationError("Value must be a string")
        
        if 'min_length' in validation and len(value) < validation['min_length']:
            raise ValidationError(f"Minimum length is {validation['min_length']}")
        
        if 'max_length' in validation and len(value) > validation['max_length']:
            raise ValidationError(f"Maximum length is {validation['max_length']}")
        
        if 'pattern' in validation and validation['pattern']:
            import re
            if not re.match(validation['pattern'], value):
                raise ValidationError("Value does not match required pattern")

from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class DataSubmission(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    )

    template = models.ForeignKey('Template', on_delete=models.PROTECT)
    department = models.ForeignKey('user_management.Department', on_delete=models.PROTECT)
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
        permissions = [
            ("can_verify_submission", "Can verify submission"),
            ("can_view_all_submissions", "Can view all submissions"),
        ]

    @property
    def board(self):
        """Retrieve the board associated with this submission's template."""
        return self.template.criteria.board

    def __str__(self):
        return f"{self.template.code} - {self.department.name} ({self.academic_year})"

    def clean(self):
        """
        Validation logic for DataSubmission:
        - Ensure only IQAC directors can verify submissions.
        - Ensure submissions can only be verified if they are in the 'submitted' state.
        """
        if self.verified_by and not self.verified_by.has_role('IQAC Director'):
            raise ValidationError("Only IQAC directors can verify submissions.")
        
        if self.verified_by and self.status == 'draft':
            raise ValidationError("Cannot verify a draft submission.")

    def get_status_display_class(self):
        """Generate a CSS class based on the status."""
        return f'status-{self.status.lower()}'

    def can_be_verified(self):
        """Check if the submission can be verified."""
        return self.status == 'submitted'

    def can_be_edited(self):
        """Check if the submission can be edited."""
        return self.status in ['draft', 'rejected']

    def get_data_summary(self):
        """Returns a summary of the submission data."""
        total_rows = self.data_rows.count()
        sections = self.data_rows.values('section_index').distinct().count()
        return f"{total_rows} rows across {sections} sections"

    def get_latest_history(self):
        """Returns the latest history entry."""
        return self.history.first()

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

    def __str__(self):
        return f"Data for {self.submission} (Section {self.section_index}, Row {self.row_number})"
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
              
class SubmissionHistory(models.Model):
    submission = models.ForeignKey('DataSubmission', on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=50)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    performed_at = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(null=True, blank=True)
    previous_data = models.JSONField(null=True, blank=True)  # Store previous state
    new_data = models.JSONField(null=True, blank=True)      # Store new state

    class Meta:
        ordering = ['-performed_at']