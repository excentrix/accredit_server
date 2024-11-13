# api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views.template import TemplateViewSet, TemplateDataViewSet
from api.views.auth import LoginView, LogoutView, UserViewSet

router = DefaultRouter()
router.register(r'templates', TemplateViewSet)
router.register(r'template-data', TemplateDataViewSet, basename='template-data')
router.register(r'users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
]