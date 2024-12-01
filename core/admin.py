# core/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Criteria,  AcademicYear, Template, DataSubmission, SubmissionData, Board
from django.utils.safestring import mark_safe
import json
from django.utils import timezone
from django.urls import reverse
from django.utils.html import format_html


@admin.register(Criteria)
class CriteriaAdmin(admin.ModelAdmin):
    list_display = ('board', 'number', 'name', 'description')
    search_fields = ('name', 'number')

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
    list_display = (
        'id',
        'template_code',
        'department_name',
        'academic_year',
        'status',
        'submitted_by_user',
        'submitted_at',
        'verified_by_user',
        'view_data_rows'
    )
    list_filter = (
        'status',
        'department',
        'academic_year',
        'template__code',
        'submitted_at',
        'verified_at'
    )
    search_fields = (
        'department__name',
        'template__code',
        'template__name',
        'submitted_by__username',
        'verified_by__username'
    )
    readonly_fields = (
        'submitted_at',
        'verified_at',
        'created_at',
        'updated_at',
        'data_preview'
    )
    fieldsets = (
        (None, {
            'fields': (
                'template',
                'department',
                'academic_year',
                'status',
            )
        }),
        ('Submission Details', {
            'fields': (
                'submitted_by',
                'submitted_at',
                'verified_by',
                'verified_at',
                'rejection_reason',
            )
        }),
        ('Data Preview', {
            'fields': ('data_preview',),
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',),
        }),
    )

    def template_code(self, obj):
        return obj.template.code
    template_code.short_description = 'Template Code'
    template_code.admin_order_field = 'template__code'

    def department_name(self, obj):
        return obj.department.name
    department_name.short_description = 'Department'
    department_name.admin_order_field = 'department__name'

    def submitted_by_user(self, obj):
        if obj.submitted_by:
            return f"{obj.submitted_by} ({obj.submitted_by.username})"
        return '-'
    submitted_by_user.short_description = 'Submitted By'
    submitted_by_user.admin_order_field = 'submitted_by__username'

    def verified_by_user(self, obj):
        if obj.verified_by:
            return f"{obj.verified_by.get_full_name()} ({obj.verified_by.username})"
        return '-'
    verified_by_user.short_description = 'Verified By'
    verified_by_user.admin_order_field = 'verified_by__username'

    def view_data_rows(self, obj):
        url = reverse('admin:core_submissiondata_changelist')
        return format_html(
            '<a href="{}?submission__id={}" class="button" style="white-space:nowrap;">View Data Rows</a>',
            url,
            obj.id
        )
    view_data_rows.short_description = 'Data Rows'

    def data_preview(self, obj):
        data_rows = obj.data_rows.all()
        if not data_rows:
            return "No data rows available"
        
        html = ['<div style="max-height: 400px; overflow-y: auto;">']
        for row in data_rows:
            html.append(f'<div style="margin-bottom: 20px;">')
            html.append(f'<h4>Section {row.section_index + 1}, Row {row.row_number}</h4>')
            html.append('<pre style="background-color: #f5f5f5; padding: 10px; border-radius: 4px;">')
            html.append(json.dumps(row.data, indent=2))
            html.append('</pre>')
            html.append('</div>')
        html.append('</div>')
        
        return mark_safe(''.join(html))
    data_preview.short_description = 'Data Preview'

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new submission
            obj.submitted_by = request.user
        
        if 'status' in form.changed_data:
            if obj.status == 'submitted' and not obj.submitted_at:
                obj.submitted_at = timezone.now()
            elif obj.status == 'approved' and not obj.verified_at:
                obj.verified_by = request.user
                obj.verified_at = timezone.now()
        
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'template',
            'department',
            'academic_year',
            'submitted_by',
            'verified_by'
        )

    class Media:
        css = {
            'all': [
                'admin/css/custom.css',
            ]
        }

@admin.register(SubmissionData)
class SubmissionDataAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_template', 'get_department', 'section_index', 'row_number', 'formatted_data', 'created_at')
    list_filter = (
        'submission__template__code',
        'submission__department',
        'submission__academic_year',
        'section_index'
    )
    search_fields = (
        'submission__template__code',
        'submission__department__name',
        'submission__academic_year__name'
    )
    readonly_fields = ('created_at', 'updated_at', 'formatted_data')

    def get_template(self, obj):
        return obj.submission.template.code
    get_template.short_description = 'Template'
    get_template.admin_order_field = 'submission__template__code'

    def get_department(self, obj):
        return obj.submission.department.name
    get_department.short_description = 'Department'
    get_department.admin_order_field = 'submission__department__name'

    def formatted_data(self, obj):
        if obj.data:
            try:
                return mark_safe(f'<pre style="max-height: 300px; overflow-y: auto;">{json.dumps(obj.data, indent=2)}</pre>')
            except:
                return str(obj.data)
        return '-'
    formatted_data.short_description = 'Data'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'submission',
            'submission__template',
            'submission__department',
            'submission__academic_year'
        )

    class Media:
        css = {
            'all': ['admin/css/custom.css']
        }

@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
