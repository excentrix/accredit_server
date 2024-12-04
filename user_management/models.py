# user_management/models.py updates
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.core.cache import cache
from django.conf import settings
from django.core.exceptions import ValidationError
import uuid

class AuditModelMixin(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,  # Allow blank values
        related_name='%(class)s_created'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,  # Allow blank values
        related_name='%(class)s_updated'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def soft_delete(self, user=None):
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        if user:
            self.updated_by = user
        self.save()

    def save(self, *args, **kwargs):
        if not self.created_by:
            self.created_by = kwargs.pop('user', None)
        self.updated_by = kwargs.pop('user', None)
        super().save(*args, **kwargs)

class Department(AuditModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name

class Module(AuditModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name

class Role(AuditModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    permissions = models.ManyToManyField('Permission', related_name='roles', blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name

class Permission(AuditModelMixin):
    ACTION_CHOICES = [
        ('view', 'View'),
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('execute', 'Execute'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(
        Module, 
        on_delete=models.CASCADE,
        related_name='permissions',
        null=True,
        blank=True
    )
    resource = models.CharField(max_length=50)
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        default='view'
    )
    codename = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['module', 'resource', 'action']
        ordering = ['module', 'resource', 'action']
        indexes = [
            models.Index(fields=['resource']),
            models.Index(fields=['action']),
            models.Index(fields=['codename']),
            models.Index(fields=['is_active']),
        ]

    def clean(self):
        if not self.codename:
            self.codename = f"{self.module.name}:{self.resource}:{self.action}"
        
        if not self.resource.isalnum() and not '_' in self.resource:
            raise ValidationError({
                'resource': 'Resource name must contain only alphanumeric characters and underscores'
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        
        # Clear related caches
        cache.delete_many('permission_*')
        cache.delete_many('user_permissions_*')

    def __str__(self):
        return f"{self.module.name}: {self.resource}:{self.action}"

class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, usn, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        if not usn:
            raise ValueError('The USN field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, usn=usn, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, usn, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, username, usn, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=50)
    usn = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    roles = models.ManyToManyField(Role, related_name='users')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    individual_permissions = models.ManyToManyField(Permission, related_name='users', blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'usn']
    

    def __str__(self):
        return self.email

    def has_role(self, role_name):
        return self.roles.filter(name=role_name).exists()
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    def get_roles_display(self):
        return ', '.join([role.name for role in self.roles.all()])

    def has_permission(self, resource, action):
        # Check if the user has individual permissions
        if self.individual_permissions.filter(resource=resource, action=action).exists():
            return True
        # Check if any of the user's roles has the required permission
        for role in self.roles.all():
            if role.permissions.filter(resource=resource, action=action).exists():
                return True
        return False

    def has_permission(self, resource, action):
        cache_key = f'user_perm_{self.id}_{resource}_{action}'
        cached_result = cache.get(cache_key)
        
        if cached_result is not None:
            return cached_result

        # Check individual permissions first
        has_perm = self.individual_permissions.filter(
            resource=resource, 
            action=action
        ).exists()

        if not has_perm:
            # Check role-based permissions
            has_perm = self.roles.filter(
                permissions__resource=resource,
                permissions__action=action
            ).exists()

        # Cache the result for 5 minutes
        cache.set(cache_key, has_perm, 300)
        return has_perm

    def clear_permission_cache(self):
        """Clear all cached permissions for this user"""
        cache_keys = cache.keys(f'user_perm_{self.id}_*')
        cache.delete_many(cache_keys)

    @property
    def role_names(self):
        """Get all role names for the user"""
        return list(self.roles.values_list('name', flat=True))

    def validate_password(self, password):
        """
        Validate password complexity requirements
        """
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        if not any(char.isdigit() for char in password):
            raise ValidationError("Password must contain at least one number.")
        if not any(char.isupper() for char in password):
            raise ValidationError("Password must contain at least one uppercase letter.")
        if not any(char.islower() for char in password):
            raise ValidationError("Password must contain at least one lowercase letter.")