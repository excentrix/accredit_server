# core/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Department, AcademicYear, Template, DataSubmission, SubmissionData

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'department', 'is_staff')
    list_filter = ('role', 'department', 'is_staff', 'is_superuser')
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'department')}),
    )

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')

@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_current')
    list_filter = ('is_current',)

@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'created_at', 'updated_at')
    search_fields = ('code', 'name')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(DataSubmission)
class DataSubmissionAdmin(admin.ModelAdmin):
    list_display = ('department', 'template', 'academic_year', 'status', 'submitted_at')
    list_filter = ('status', 'department', 'academic_year')
    search_fields = ('department__name', 'template__code')
    readonly_fields = ('submitted_at', 'verified_at')

@admin.register(SubmissionData)
class SubmissionDataAdmin(admin.ModelAdmin):
    list_display = ('submission', 'row_number', 'created_at')
    list_filter = ('submission__department', 'submission__academic_year')
    readonly_fields = ('created_at', 'updated_at')