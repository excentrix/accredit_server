# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from .models import CustomUser, Department, Module, Permission, Role, AuditLog
from django.db.models import Q

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
    
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        'created_at',
        'get_user_link',
        'action',
        'module',
        'status',
        'ip_address',
        'get_details_preview',
    )
    
    list_filter = (
        'action',
        'module',
        'status',
        'created_at',
    )
    
    search_fields = (
        'user__email',
        'user__username',
        'module',
        'ip_address',
        'details',
    )
    
    readonly_fields = (
        'id',
        'user',
        'action',
        'module',
        'details',
        'ip_address',
        'user_agent',
        'status',
        'created_at',
        'updated_at',
    )
    
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'id',
                'user',
                'action',
                'module',
                'status',
            )
        }),
        ('Details', {
            'fields': (
                'details',
            ),
            'classes': ('collapse',),
        }),
        ('System Information', {
            'fields': (
                'ip_address',
                'user_agent',
            ),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            ),
        }),
    )

    def get_user_link(self, obj):
        if obj.user:
            # Construct the URL pattern based on your user model
            # Format: admin:{app_label}_{model_name}_change
            url = reverse(
                f'admin:{obj.user._meta.app_label}_{obj.user._meta.model_name}_change',
                args=[obj.user.id]
            )
            return format_html('<a href="{}">{}</a>', url, obj.user)
        return "Unknown User"
    get_user_link.short_description = 'User'
    get_user_link.admin_order_field = 'user'


    def get_details_preview(self, obj):
        if obj.details:
            # Convert the details to a string and limit its length
            preview = str(obj.details)
            max_length = 50
            if len(preview) > max_length:
                preview = preview[:max_length] + '...'
            return preview
        return '-'
    get_details_preview.short_description = 'Details Preview'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete audit logs
        return request.user.is_superuser

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # If user is not superuser, limit to their own logs
        if not request.user.is_superuser:
            qs = qs.filter(Q(user=request.user) | Q(user__isnull=True))
        return qs

    # class Media:
    #     css = {
    #         'all': ('admin/css/audit_log.css',)
    #     }
    #     js = ('admin/js/audit_log.js',)