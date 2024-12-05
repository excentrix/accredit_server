# core/validators.py
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re
import json
from datetime import datetime

class TemplateValidator:
    """Validates template structure and data"""
    
    @staticmethod
    def validate_template_structure(metadata):
        if not isinstance(metadata, list):
            raise ValidationError(_("Template metadata must be a list of sections"))
            
        for section_index, section in enumerate(metadata):
            TemplateValidator._validate_section(section, section_index)
    
    @staticmethod
    def _validate_section(section, section_index):
        required_keys = {'headers', 'columns'}
        if not all(key in section for key in required_keys):
            raise ValidationError(_(f"Section {section_index}: Missing required keys {required_keys}"))
            
        if not isinstance(section['headers'], list):
            raise ValidationError(_(f"Section {section_index}: Headers must be a list"))
            
        if not isinstance(section['columns'], list):
            raise ValidationError(_(f"Section {section_index}: Columns must be a list"))
            
        for column in section['columns']:
            TemplateValidator._validate_column(column, section_index)
    
    @staticmethod
    def _validate_column(column, section_index):
        required_keys = {'name', 'type', 'display_name'}
        if not all(key in column for key in required_keys):
            raise ValidationError(_(f"Section {section_index}: Column missing required keys {required_keys}"))
            
        if column['type'] not in ['text', 'number', 'date', 'select', 'file', 'boolean']:
            raise ValidationError(_(f"Section {section_index}: Invalid column type {column['type']}"))
            
        if column['type'] == 'select' and 'options' not in column:
            raise ValidationError(_(f"Section {section_index}: Select column must have options"))

class DataValidator:
    """Validates submission data against template structure"""
    
    @staticmethod
    def validate_submission_data(template, data, section_index):
        if section_index >= len(template.metadata):
            raise ValidationError(_("Invalid section index"))
            
        section = template.metadata[section_index]
        columns = DataValidator._get_flattened_columns(section['columns'])
        
        # Validate required fields
        for column in columns:
            if column.get('required', False):
                if column['name'] not in data or not data[column['name']]:
                    raise ValidationError(_(f"Required field missing: {column['name']}"))
                    
            if column['name'] in data:
                DataValidator._validate_field_value(data[column['name']], column)
    
    @staticmethod
    def _validate_field_value(value, column):
        if value is None or value == '':
            if column.get('required', False):
                raise ValidationError(_(f"Required field empty: {column['name']}"))
            return

        try:
            if column['type'] == 'number':
                DataValidator._validate_number(value, column.get('validation', {}))
            elif column['type'] == 'date':
                DataValidator._validate_date(value)
            elif column['type'] == 'select':
                DataValidator._validate_select(value, column.get('options', []))
            elif column['type'] == 'boolean':
                DataValidator._validate_boolean(value)
            elif column['type'] == 'file':
                DataValidator._validate_file(value, column.get('validation', {}))
        except ValidationError as e:
            raise ValidationError(_(f"{column['name']}: {str(e)}"))

    @staticmethod
    def _validate_number(value, validation):
        try:
            num_value = float(value)
            if 'min' in validation and num_value < validation['min']:
                raise ValidationError(_(f"Value must be >= {validation['min']}"))
            if 'max' in validation and num_value > validation['max']:
                raise ValidationError(_(f"Value must be <= {validation['max']}"))
        except (TypeError, ValueError):
            raise ValidationError(_("Invalid number format"))

    @staticmethod
    def _validate_date(value):
        try:
            if isinstance(value, str):
                datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            raise ValidationError(_("Invalid date format. Use YYYY-MM-DD"))

    @staticmethod
    def _validate_select(value, options):
        if value not in options:
            raise ValidationError(_(f"Value must be one of: {', '.join(options)}"))

    @staticmethod
    def _validate_boolean(value):
        if not isinstance(value, bool):
            raise ValidationError(_("Value must be true or false"))

    @staticmethod
    def _validate_file(value, validation):
        allowed_extensions = validation.get('allowed_extensions', [])
        max_size = validation.get('max_size', 5 * 1024 * 1024)  # Default 5MB
        
        if not value:
            return
            
        file_extension = value.name.split('.')[-1].lower()
        if allowed_extensions and file_extension not in allowed_extensions:
            raise ValidationError(_(f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"))
            
        if value.size > max_size:
            raise ValidationError(_(f"File size too large. Maximum size: {max_size/1024/1024}MB"))