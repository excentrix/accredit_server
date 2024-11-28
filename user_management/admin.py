# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from .models import CustomUser, Department, Module, Permission, Role

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['email', 'username', 'get_roles_display', 'department', 'is_staff', 'is_active', 'last_login']
    list_filter = ['roles', 'department', 'is_staff', 'is_active', 'date_joined']
    readonly_fields = ['date_joined', 'last_login']
    search_fields = ['email', 'username', 'usn', 'roles__name']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal info', {'fields': ('usn', 'department')}),
        ('Roles and Permissions', {
            'fields': ('roles', 'individual_permissions'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_staff', 'is_superuser'),
            'classes': ('collapse',)
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'usn', 'password1', 'password2', 'department', 'roles', 'is_active')}
        ),
    )

    def get_roles_display(self, obj):
        roles = obj.roles.all()
        return format_html(', '.join([f'<span style="background-color: #f0f0f0; padding: 2px 6px; border-radius: 3px;">{role.name}</span>' for role in roles]))
    get_roles_display.short_description = 'Roles'

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'get_users_count']
    search_fields = ['name', 'code']
    
    def get_users_count(self, obj):
        return obj.users.count()
    get_users_count.short_description = 'Users Count'

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'get_permissions_count']
    search_fields = ['name']
    
    def get_permissions_count(self, obj):
        return obj.permissions.count()
    get_permissions_count.short_description = 'Permissions Count'

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['codename', 'module', 'resource', 'action', 'created_at']
    list_filter = ['module', 'action', 'created_at']
    search_fields = ['codename', 'module__name', 'resource']
    readonly_fields = ['codename', 'created_at', 'updated_at']
    ordering = ['module', 'resource', 'action']
    
    fieldsets = (
        (None, {
            'fields': ('module', 'resource', 'action')
        }),
        ('Additional Information', {
            'fields': ('description', 'codename'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'get_users_count', 'get_permissions_count']
    search_fields = ['name']
    filter_horizontal = ['permissions']
    
    def get_users_count(self, obj):
        return obj.users.count()
    get_users_count.short_description = 'Users'
    
    def get_permissions_count(self, obj):
        return obj.permissions.count()
    get_permissions_count.short_description = 'Permissions'