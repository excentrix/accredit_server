# core/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CriteriaViewSet, DepartmentViewSet, AcademicYearViewSet, NameAutocompleteView,
    TemplateViewSet, DataSubmissionViewSet,
    ExportTemplateView, Board
)

from .views import AuthViewSet, UserViewSet, TemplateViewSet, DataSubmissionViewSet, BoardViewSet

import logging

logger = logging.getLogger(__name__)

router = DefaultRouter()
router.register(r'departments', DepartmentViewSet)
router.register(r'academic-years', AcademicYearViewSet, basename='academic-year')
router.register(r'submissions', DataSubmissionViewSet, basename='submission')
router.register(r'criteria/list', CriteriaViewSet, basename='criteria')
# router.register(r'auth', TemplateViewSet, basename='template')

urlpatterns = [
    path('', include(router.urls)),
    # path('export/', ExportTemplateView.as_view(), name='export-template'),
    path('auth/login/', AuthViewSet.as_view({'post': 'login'})),
    path('auth/logout/', AuthViewSet.as_view({'post': 'logout'})),
    path('auth/me/', AuthViewSet.as_view({'get': 'me'})),
    path('auth/token/refresh/', AuthViewSet.as_view({'post':'refresh'}), name='token_refresh'),
    path('submissions/stats/', DataSubmissionViewSet.as_view({'get': 'stats'}), name='submission-stats'),
    path('submissions/department-breakdown/', DataSubmissionViewSet.as_view({'get': 'department_breakdown'}), name='department_breakdown'),
    
    path('boards/', BoardViewSet.as_view(), name='board-list'),
    path(
        'boards/<str:code>/criteria/',
        CriteriaViewSet.as_view({'get': 'list'}),
        name='board-criteria'
    ),
    path(
        'boards/<str:code>/templates/',
        TemplateViewSet.as_view({'get': 'list'}),
        name='board-templates'
    ),
    path('templates/', TemplateViewSet.as_view({'get': 'list', 'post': 'create'}), name='template-list'),
    path('templates/export/', ExportTemplateView.as_view(), name='template-export'),
    path('templates/import-excel/', TemplateViewSet.as_view({
            'post': 'import_from_excel'
        }), name='template-import-excel'),
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
    path(
    'templates/<str:code>/submission/',
    TemplateViewSet.as_view({
        'get': 'submission_state',
        'post': 'submission_state'  # Changed from 'create_submission' to match viewset
    }),
    name='template-submission'
    ),
    
    path(
    'templates/<str:code>/submit/',
    TemplateViewSet.as_view({
        'post': 'submit_template'  # This matches your viewset method name
    }),
    name='template-submit'
    ),    
    
    path(
    'templates/<str:code>/withdraw/',
    TemplateViewSet.as_view({
        'post': 'withdraw_submission'
    }),
    name='template-withdraw'
    ),
    path(
    'templates/<str:code>/approve/',
    TemplateViewSet.as_view({
        'post': 'approve_submission'
    }),
    name='template-approve'
    ),

    path(
    'templates/<str:code>/reject/',
    TemplateViewSet.as_view({
        'post': 'reject_submission'
    }),
    name='template-reject'
    ),
    path('templates/<str:code>/data/row/', TemplateViewSet.as_view({
        'put': 'data_row',
        'delete': 'data_row'
    }), name='template-data-row'),
    path(
        'templates/<str:code>/sections/<int:section_index>/data/',
        TemplateViewSet.as_view({
            'get': 'section_data',
            'post': 'section_data'
        }),
        name='template-section-data'
    ),

    
    # Section-specific row operations
    path(
        'templates/<str:code>/sections/<int:section_index>/data/<int:row_id>/',
        TemplateViewSet.as_view({
            'put': 'section_data_row',
            'delete': 'section_data_row'
        }),
        name='template-section-data-row'
    ),
    

    path('autocomplete/', NameAutocompleteView.as_view(), name='name-autocomplete'),
]

logger.debug("Core URL patterns: %s", urlpatterns)