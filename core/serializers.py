from rest_framework import serializers
from .models import User, Department, AcademicYear, Template, DataSubmission, SubmissionData

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Department, Template, DataSubmission

User = get_user_model()

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'code']

class UserSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                 'role', 'department']
        read_only_fields = ['id']

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

class AcademicYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicYear
        fields = ['id', 'year', 'is_current']

class TemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Template
        fields = ['id', 'code', 'name', 'description', 'headers', 'columns']

    def validate_columns(self, value):
        required_keys = {'name', 'display_name', 'type'}
        for column in value:
            if not all(key in column for key in required_keys):
                raise serializers.ValidationError(
                    "Each column must contain 'name', 'display_name', and 'type'"
                )
        return value

class SubmissionDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubmissionData
        fields = ['id', 'row_number', 'data', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class DataSubmissionSerializer(serializers.ModelSerializer):
    department_details = DepartmentSerializer(source='department', read_only=True)
    template_details = TemplateSerializer(source='template', read_only=True)
    academic_year_details = AcademicYearSerializer(source='academic_year', read_only=True)
    submitted_by_details = UserSerializer(source='submitted_by', read_only=True)
    verified_by_details = UserSerializer(source='verified_by', read_only=True)
    data_rows = SubmissionDataSerializer(many=True, read_only=True)

    class Meta:
        model = DataSubmission
        fields = [
            'id', 'department', 'department_details',
            'academic_year', 'academic_year_details',
            'template', 'template_details',
            'submitted_by', 'submitted_by_details',
            'verified_by', 'verified_by_details',
            'status', 'submitted_at', 'verified_at',
            'rejection_reason', 'data_rows'
        ]
        read_only_fields = ['submitted_at', 'verified_at', 'submitted_by', 'verified_by']