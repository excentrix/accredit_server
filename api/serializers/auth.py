# api/serializers/auth.py
from rest_framework import serializers
from core.models.user import User
from core.models.department import Department

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'code']

class UserSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'full_name', 'role', 'department', 'phone_number', 
             'employee_id'
        ]
        read_only_fields = ['role']

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)