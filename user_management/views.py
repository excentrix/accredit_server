# user_management/views.py
import logging
from django.db import transaction
from django.core.cache import cache
from rest_framework import viewsets, generics, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import CustomUser, Role, Permission, Department
from .serializers import (
    UserRegistrationSerializer, 
    UserSerializer, 
    RoleSerializer, 
    PermissionSerializer,
    CustomTokenObtainPairSerializer
)
from .permissions import HasDynamicPermission, IsAdmin, HasPermission, IsFaculty, IsStudent

logger = logging.getLogger(__name__)

class StandardResultsSetPagination:
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class StandardResponse:
    @staticmethod
    def success(data=None, message=None, status_code=status.HTTP_200_OK):
        return Response({
            'status': 'success',
            'message': message,
            'data': data
        }, status=status_code)

    @staticmethod
    def error(message, status_code=status.HTTP_400_BAD_REQUEST):
        return Response({
            'status': 'error',
            'message': str(message)
        }, status=status_code)

class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [HasPermission]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['department', 'is_active', 'roles']
    search_fields = ['email', 'username', 'usn']
    ordering_fields = ['date_joined', 'username', 'email']

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.has_role('admin'):
            queryset = queryset.filter(department=self.request.user.department)
        return queryset

    def get_permissions(self):
        if self.action in ['list', 'create', 'destroy', 'assign_role', 'revoke_role']:
            permission_classes = [IsAdmin]
        elif self.action in ['retrieve', 'update', 'partial_update']:
            permission_classes = [HasPermission]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                user = serializer.save()
                logger.info(f"User created successfully: {user.username}")
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise ValidationError(str(e))

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def assign_role(self, request, pk=None):
        try:
            with transaction.atomic():
                user = self.get_object()
                role_name = request.data.get('role')
                if not role_name:
                    raise ValidationError("Role name is required")

                role = Role.objects.get(name=role_name)
                user.roles.add(role)
                
                # Clear user's permission cache
                cache_key = f"user_permissions_{user.id}"
                cache.delete(cache_key)
                
                logger.info(f"Role {role_name} assigned to user {user.username}")
                return StandardResponse.success(
                    UserSerializer(user).data,
                    message=f'Role {role_name} assigned to user {user.username}'
                )
        except Role.DoesNotExist:
            logger.warning(f"Role not found: {role_name}")
            raise NotFound(f"Role '{role_name}' not found.")
        except Exception as e:
            logger.error(f"Error assigning role: {str(e)}")
            return StandardResponse.error(str(e))

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def revoke_role(self, request, pk=None):
        try:
            with transaction.atomic():
                user = self.get_object()
                role_name = request.data.get('role')
                if not role_name:
                    raise ValidationError("Role name is required")

                role = Role.objects.get(name=role_name)
                user.roles.remove(role)
                
                # Clear user's permission cache
                cache_key = f"user_permissions_{user.id}"
                cache.delete(cache_key)
                
                logger.info(f"Role {role_name} revoked from user {user.username}")
                return StandardResponse.success(
                    UserSerializer(user).data,
                    message=f'Role {role_name} revoked from user {user.username}'
                )
        except Role.DoesNotExist:
            logger.warning(f"Role not found: {role_name}")
            raise NotFound(f"Role '{role_name}' not found.")
        except Exception as e:
            logger.error(f"Error revoking role: {str(e)}")
            return StandardResponse.error(str(e))

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAdmin]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name']

    @action(detail=True, methods=['post'])
    def assign_permission(self, request, pk=None):
        try:
            with transaction.atomic():
                role = self.get_object()
                permission_id = request.data.get('permission_id')
                if not permission_id:
                    raise ValidationError("Permission ID is required")

                permission = Permission.objects.get(id=permission_id)
                role.permissions.add(permission)
                
                # Clear cache for all users with this role
                users = CustomUser.objects.filter(roles=role)
                for user in users:
                    cache_key = f"user_permissions_{user.id}"
                    cache.delete(cache_key)

                logger.info(f"Permission {permission.codename} assigned to role {role.name}")
                return StandardResponse.success(
                    RoleSerializer(role).data,
                    message=f'Permission {permission.codename} assigned to role {role.name}'
                )
        except Permission.DoesNotExist:
            return StandardResponse.error('Permission not found', status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error assigning permission: {str(e)}")
            return StandardResponse.error(str(e))

    @action(detail=True, methods=['post'])
    def revoke_permission(self, request, pk=None):
        try:
            with transaction.atomic():
                role = self.get_object()
                permission_id = request.data.get('permission_id')
                if not permission_id:
                    raise ValidationError("Permission ID is required")

                permission = Permission.objects.get(id=permission_id)
                role.permissions.remove(permission)
                
                # Clear cache for all users with this role
                users = CustomUser.objects.filter(roles=role)
                for user in users:
                    cache_key = f"user_permissions_{user.id}"
                    cache.delete(cache_key)

                logger.info(f"Permission {permission.codename} revoked from role {role.name}")
                return StandardResponse.success(
                    RoleSerializer(role).data,
                    message=f'Permission {permission.codename} revoked from role {role.name}'
                )
        except Permission.DoesNotExist:
            return StandardResponse.error('Permission not found', status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error revoking permission: {str(e)}")
            return StandardResponse.error(str(e))

class PermissionViewSet(viewsets.ModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAdmin]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['module', 'resource', 'action']
    search_fields = ['codename', 'description']
    ordering_fields = ['codename', 'module', 'resource']

class UserRegistrationView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                user = serializer.save()
                logger.info(f"New user registered: {user.email}")
        except Exception as e:
            logger.error(f"Error during user registration: {str(e)}")
            raise ValidationError(str(e))

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class ModuleResourceView(APIView):
    permission_classes = [HasDynamicPermission]
    resource = 'module'
    action = 'view'

    def get(self, request):
        try:
            # Add your business logic here
            return StandardResponse.success(
                message='You have permission to view this resource.'
            )
        except Exception as e:
            logger.error(f"Error in ModuleResourceView: {str(e)}")
            return StandardResponse.error(str(e))