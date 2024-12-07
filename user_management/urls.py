# user_management/urls.py

from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,TokenBlacklistView 
)
from .views import ChangePasswordView, PasswordResetConfirmView, PasswordResetRequestView, UserDetailView, UserRegistrationView, UserViewSet, RoleViewSet, PermissionViewSet, DepartmentViewSet, AuditLogViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'permissions', PermissionViewSet, basename='permission')
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'audit-logs', AuditLogViewSet, basename='audit-logs')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', TokenBlacklistView.as_view(), name='token_blacklist'),
    path('reset-password-request/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('reset-password/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('users/me/', UserDetailView.as_view(), name='user_detail'),
]
