# api/filters.py
import django_filters
from core.models.template import Template, TemplateData
from core.models.user import User

class TemplateFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains')
    file_code = django_filters.CharFilter(lookup_expr='icontains')
    created_after = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = Template
        fields = ['type', 'is_active', 'title', 'file_code']

class TemplateDataFilter(django_filters.FilterSet):
    created_after = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    department_code = django_filters.CharFilter(field_name='department__code')

    class Meta:
        model = TemplateData
        fields = ['template', 'department', 'academic_year', 'status']

class UserFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(method='filter_name')
    
    class Meta:
        model = User
        fields = ['role', 'department', 'is_active']
    
    def filter_name(self, queryset, name, value):
        return queryset.filter(
            models.Q(first_name__icontains=value) |
            models.Q(last_name__icontains=value)
        )