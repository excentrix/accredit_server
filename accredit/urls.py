# accredit/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from monitoring.views import HealthCheckView

schema_view = get_schema_view(
    openapi.Info(
        title="Accredit API",
        default_version='v1',
        description="API documentation for your project",
        terms_of_service="https://www.excentrix.tech/terms/",
        contact=openapi.Contact(email="hello@excentrix.tech"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    path('user/', include('user_management.urls')),
    path('health/', HealthCheckView.as_view(), name='health_check'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)