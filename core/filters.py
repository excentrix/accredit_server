from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter
from .models import DataSubmission, Department, Template, AcademicYear
from django.db import models

class DataSubmissionFilter(filters.FilterSet):
    # Academic Year filters
    academic_year = filters.ModelChoiceFilter(queryset=AcademicYear.objects.all())
    is_current_year = filters.BooleanFilter(field_name='academic_year__is_current')
    
    # Department filters
    department = filters.ModelChoiceFilter(queryset=Department.objects.all())
    department_code = filters.CharFilter(field_name='department__code')
    
    # Template filters
    template = filters.ModelChoiceFilter(queryset=Template.objects.all())
    template_code = filters.CharFilter(field_name='template__code')
    
    # Status filters
    status = filters.ChoiceFilter(choices=DataSubmission.STATUS_CHOICES)
    
    # Date filters
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    submitted_after = filters.DateTimeFilter(field_name='submitted_at', lookup_expr='gte')
    submitted_before = filters.DateTimeFilter(field_name='submitted_at', lookup_expr='lte')
    verified_after = filters.DateTimeFilter(field_name='verified_at', lookup_expr='gte')
    verified_before = filters.DateTimeFilter(field_name='verified_at', lookup_expr='lte')
    
    # User filters
    submitted_by = filters.NumberFilter(field_name='submitted_by__id')
    verified_by = filters.NumberFilter(field_name='verified_by__id')

    # Search filters
    search = filters.CharFilter(method='filter_search')

    # Board filters
    board = filters.CharFilter(field_name='board')

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            models.Q(template__name__icontains=value) |
            models.Q(department__name__icontains=value) |
            models.Q(submitted_by__username__icontains=value) |
            models.Q(template__code__icontains=value) |
            models.Q(board__icontains=value) 
        )

    class Meta:
        model = DataSubmission
        fields = {
            'academic_year': ['exact'],
            'department': ['exact'],
            'template': ['exact'],
            'status': ['exact'],
            'board': ['exact'],
            'created_at': ['exact', 'lt', 'gt', 'lte', 'gte'],
            'submitted_at': ['exact', 'lt', 'gt', 'lte', 'gte'],
            'verified_at': ['exact', 'lt', 'gt', 'lte', 'gte'],
        }