# core/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from core.models.user import User
from core.models.department import Department
from core.models.template import Template, TemplateData

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'department']
    list_filter = ['role', 'department', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'employee_id']
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Information', {
            'fields': ('role', 'department'),
        }),
    )

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'hod', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']

@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = ['file_code', 'title', 'type', 'is_active', 'deadline']
    list_filter = ['type', 'is_active']
    search_fields = ['file_code', 'title']

@admin.register(TemplateData)
class TemplateDataAdmin(admin.ModelAdmin):
    list_display = [
        'template', 'department', 'academic_year', 
        'status', 'submitted_by', 'created_at'
    ]
    list_filter = ['status', 'department', 'academic_year']
    search_fields = ['template__file_code', 'department__name']
    raw_id_fields = ['template', 'department', 'submitted_by', 'reviewed_by']