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
        fields = ['id', 'name', 'start_date', 'end_date', 'is_current']

class TemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Template
        fields = ['id', 'code', 'name', 'metadata']

    # def validate_columns(self, value):
    #     required_keys = {'name', 'display_name', 'type'}
    #     for column in value:
    #         if not all(key in column for key in required_keys):
    #             raise serializers.ValidationError(
    #                 "Each column must contain 'name', 'display_name', and 'type'"
    #             )
    #     return value

class SubmissionDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubmissionData
        fields = ['section_index', 'row_number', 'data']

class DataSubmissionSerializer(serializers.ModelSerializer):
    data_rows = SubmissionDataSerializer(many=True, read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True)
    submitted_by_name = serializers.CharField(source='submitted_by.get_full_name', read_only=True)
    academic_year_name = serializers.CharField(source='academic_year.name', read_only=True)
    
    class Meta:
        model = DataSubmission
        fields = [
            'id', 'template', 'department', 'academic_year', 'academic_year_name',
            'status', 'submitted_at', 'verified_by', 'verified_at', 
            'rejection_reason', 'data_rows', 'department_name', 
            'template_name', 'submitted_by_name'
        ]
        read_only_fields = ['submitted_by', 'verified_by', 'verified_at']

    def validate(self, data):
        # Ensure user can only submit for their department
        user = self.context['request'].user
        if user.role == 'faculty' and data['department'] != user.department:
            raise serializers.ValidationError(
                "You can only submit data for your own department"
            )
        return data