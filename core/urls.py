# core/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DepartmentViewSet, AcademicYearViewSet,
    TemplateViewSet, DataSubmissionViewSet,
    ExportTemplateView
)

from .views import AuthViewSet, UserViewSet, TemplateViewSet, DataSubmissionViewSet

import logging

logger = logging.getLogger(__name__)

router = DefaultRouter()
router.register(r'departments', DepartmentViewSet)
router.register(r'academic-years', AcademicYearViewSet)
router.register(r'templates', TemplateViewSet)
router.register(r'submissions', DataSubmissionViewSet, basename='submission')

urlpatterns = [
    path('', include(router.urls)),
    path('export/', ExportTemplateView.as_view(), name='export-template'),
    path('auth/login/', AuthViewSet.as_view({'post': 'login'})),
    path('auth/logout/', AuthViewSet.as_view({'post': 'logout'})),
    path('auth/me/', AuthViewSet.as_view({'get': 'me'})),
]

logger.debug("Core URL patterns: %s", urlpatterns)