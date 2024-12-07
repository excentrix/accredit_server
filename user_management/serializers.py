from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import CustomUser, Role, Permission, Department, Module, AuditLog

class DepartmentSerializer(serializers.ModelSerializer):
    users_count = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = ['id', 'name', 'code', 'users_count']

    def get_users_count(self, obj):
        return obj.users.count()

    def validate_code(self, value):
        if not value.isalnum():
            raise serializers.ValidationError("Department code must be alphanumeric")
        return value.upper()

class ModuleSerializer(serializers.ModelSerializer):
    permissions_count = serializers.SerializerMethodField()
    active_permissions = serializers.SerializerMethodField()

    class Meta:
        model = Module
        fields = ['id', 'name', 'description', 'permissions_count', 'active_permissions']

    def get_permissions_count(self, obj):
        return obj.permissions.count()

    def get_active_permissions(self, obj):
        return obj.permissions.filter(is_active=True).count()

    def validate_name(self, value):
        if Module.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("A module with this name already exists")
        return value

class PermissionSerializer(serializers.ModelSerializer):
    module_name = serializers.CharField(source='module.name', read_only=True)
    full_codename = serializers.SerializerMethodField()

    class Meta:
        model = Permission
        fields = [
            'id', 'module', 'module_name', 'resource', 'action', 
            'codename', 'description', 'full_codename'
        ]
        read_only_fields = ['codename', 'full_codename']

    def get_full_codename(self, obj):
        return f"{obj.module.name}.{obj.resource}.{obj.action}"

    def validate(self, data):
        # Ensure module exists
        if not Module.objects.filter(id=data.get('module').id).exists():
            raise serializers.ValidationError("Invalid module specified")
        
        # Check for duplicate permission
        if Permission.objects.filter(
            module=data.get('module'),
            resource=data.get('resource'),
            action=data.get('action')
        ).exists():
            raise serializers.ValidationError("This permission already exists")
        
        return data

class RoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    users_count = serializers.SerializerMethodField()
    permission_ids = serializers.PrimaryKeyRelatedField(
        queryset=Permission.objects.all(),
        write_only=True,
        many=True,
        required=False,
        source='permissions'
    )

    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'permissions', 'permission_ids', 'users_count']

    def get_users_count(self, obj):
        return obj.users.count()

    def validate_name(self, value):
        if Role.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("A role with this name already exists")
        return value.lower()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    department = DepartmentSerializer(read_only=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'username', 'password', 'confirm_password', 'department', 'usn']

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        try:
            validate_password(data['password'])
        except ValidationError as e:
            raise serializers.ValidationError({'password': list(e.messages)})
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = CustomUser.objects.create_user(**validated_data)
        return user

class UserSerializer(serializers.ModelSerializer):
    roles = RoleSerializer(many=True, read_only=True)
    department = DepartmentSerializer(read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        source='department',
        write_only=True,
        required=False
    )
    role_ids = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        write_only=True,
        many=True,
        required=False,
        source='roles'
    )
    full_name = serializers.SerializerMethodField()
    # permissions = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'username', 'usn', 'department', 'department_id',
            'roles', 'role_ids', 'is_active', 'date_joined', 'last_login',
            'full_name', 
            # 'permissions'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username

    def get_permissions(self, obj):
        # Get unique permissions from all roles
        permissions = set()
        for role in obj.roles.all():
            for perm in role.permissions.all():
                permissions.add(perm.codename)
        return list(permissions)

    def validate_email(self, value):
        if CustomUser.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value.lower()

    def validate_username(self, value):
        if CustomUser.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value.lower()

    def validate_usn(self, value):
        if value and CustomUser.objects.filter(usn__iexact=value).exists():
            raise serializers.ValidationError("This USN is already registered.")
        return value.upper() if value else value

class UserDetailSerializer(UserSerializer):
    individual_permissions = PermissionSerializer(many=True, read_only=True)
    all_permissions = serializers.SerializerMethodField()
    
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['individual_permissions', 'all_permissions']

    def get_all_permissions(self, obj):
        # Combine role permissions and individual permissions
        permissions = set()
        # Add role permissions
        for role in obj.roles.all():
            for perm in role.permissions.all():
                permissions.add(perm.codename)
        # Add individual permissions
        for perm in obj.individual_permissions.all():
            permissions.add(perm.codename)
        return list(permissions)

class CustomTokenObtainPairSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email', '').lower()
        if not CustomUser.objects.filter(email=email).exists():
            raise serializers.ValidationError({
                'email': 'No account found with this email address.'
            })
        return attrs
    

class AuditLogSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    timestamp = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id',
            'user',
            'action',
            'action_display',
            'module',
            'details',
            'ip_address',
            'user_agent',
            'status',
            'timestamp',
        ]
        read_only_fields = fields

    def get_user(self, obj):
        if obj.user:
            return {
                'id': obj.user.id,
                'email': obj.user.email,
                'username': obj.user.username,
                'full_name': obj.user.get_full_name()
            }
        return None

class AuditLogSummarySerializer(serializers.Serializer):
    total_actions = serializers.IntegerField()
    actions_by_type = serializers.ListField(
        child=serializers.DictField()
    )
    actions_by_module = serializers.ListField(
        child=serializers.DictField()
    )
    actions_by_status = serializers.ListField(
        child=serializers.DictField()
    )
    top_users = serializers.ListField(
        child=serializers.DictField()
    )

    class Meta:
        fields = [
            'total_actions',
            'actions_by_type',
            'actions_by_module',
            'actions_by_status',
            'top_users'
        ]