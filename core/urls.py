# core/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DepartmentViewSet, AcademicYearViewSet, NameAutocompleteView,
    TemplateViewSet, DataSubmissionViewSet,
    ExportTemplateView
)

from .views import AuthViewSet, UserViewSet, TemplateViewSet, DataSubmissionViewSet

import logging

logger = logging.getLogger(__name__)

router = DefaultRouter()
router.register(r'departments', DepartmentViewSet)
router.register(r'academic-years', AcademicYearViewSet)
# router.register(r'templates', TemplateViewSet, basename='template')
router.register(r'submissions', DataSubmissionViewSet, basename='submission')

urlpatterns = [
    path('', include(router.urls)),
    path('export/', ExportTemplateView.as_view(), name='export-template'),
    path('auth/login/', AuthViewSet.as_view({'post': 'login'})),
    path('auth/logout/', AuthViewSet.as_view({'post': 'logout'})),
    path('auth/me/', AuthViewSet.as_view({'get': 'me'})),
    path('templates/', TemplateViewSet.as_view({'get': 'list', 'post': 'create'}), name='template-list'),
    # path('templates/import-excel/', TemplateViewSet.as_view({
    #         'post': 'import_from_excel'
    #     }), name='template-import-excel'),
        path('templates/<str:code>/', TemplateViewSet.as_view({
            'get': 'retrieve',
            'put': 'update',
            'patch': 'partial_update',
            'delete': 'destroy'
        }), name='template-detail'),
    path('templates/<str:code>/data/', TemplateViewSet.as_view({
        'get': 'data',
        'post': 'data'
    }), name='template-data'),
    path('templates/<str:code>/data/row/', TemplateViewSet.as_view({
        'put': 'data_row',
        'delete': 'data_row'
    }), name='template-data-row'),
    path('autocomplete/', NameAutocompleteView.as_view(), name='name-autocomplete'),
]

logger.debug("Core URL patterns: %s", urlpatterns)