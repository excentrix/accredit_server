from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter

from .models import DataSubmission

class DataSubmissionFilter(filters.FilterSet):
    academic_year = filters.NumberFilter(field_name='academic_year')
    department = filters.NumberFilter(field_name='department')
    template = filters.NumberFilter(field_name='template')
    status = filters.ChoiceFilter(choices=DataSubmission.STATUS_CHOICES)
    created_after = filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = DataSubmission
        fields = ['academic_year', 'department', 'template', 'status']