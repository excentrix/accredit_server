# user_management/views.py
import csv
from datetime import timedelta
from django.utils import timezone
import logging
from django.db import transaction
from django.core.cache import cache
from django.http import HttpResponse
from rest_framework import viewsets, generics, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count


from .models import AuditLog, CustomUser, Role, Permission, Department
from .serializers import (
    UserRegistrationSerializer, 
    UserSerializer, 
    RoleSerializer, 
    PermissionSerializer,
    CustomTokenObtainPairSerializer,
    DepartmentSerializer, 
    AuditLogSerializer
)
from .permissions import HasDynamicPermission, IsAdmin, HasPermission, IsFaculty, IsStudent

logger = logging.getLogger(__name__)

from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000


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
        

class UserDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            data = UserSerializer(user).data
            return StandardResponse.success(data=data, message="User details retrieved successfully")
        except Exception as e:
            logger.error(f"Error retrieving user details: {str(e)}")
            return StandardResponse.error(str(e))


class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [HasPermission]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['department', 'is_active', 'roles']
    search_fields = ['email', 'username', 'usn']
    ordering_fields = ['date_joined', 'username', 'email']
    resource = 'user'

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

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """
        Endpoint to get the current authenticated user's details.
        """
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin], url_path='assign-role')
    def assign_role(self, request, pk=None):
        try:
            with transaction.atomic():
                user = self.get_object()
                role_id = request.data.get('role_id')
                if not role_id:
                    raise ValidationError("Role name is required")

                role = Role.objects.get(id=role_id)
                user.roles.add(role)

                # Clear user's permission cache
                cache_key = f"user_permissions_{user.id}"
                cache.delete(cache_key)

                logger.info(f"Role {role_id} assigned to user {user.username}")
                return StandardResponse.success(
                    UserSerializer(user).data,
                    message=f'Role {role_id} assigned to user {user.username}'
                )
        except Role.DoesNotExist:
            logger.warning(f"Role not found: {role_id}")
            raise NotFound(f"Role '{role_id}' not found.")
        except Exception as e:
            logger.error(f"Error assigning role: {str(e)}")
            return StandardResponse.error(str(e))

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin], url_path='revoke-role')
    def revoke_role(self, request, pk=None):
        try:
            with transaction.atomic():
                user = self.get_object()
                role_id = request.data.get('role_id')
                if not role_id:
                    raise ValidationError("Role name is required")

                role = Role.objects.get(id=role_id)
                user.roles.remove(role)

                # Clear user's permission cache
                cache_key = f"user_permissions_{user.id}"
                cache.delete(cache_key)

                logger.info(f"Role {role_id} revoked from user {user.username}")
                return StandardResponse.success(
                    UserSerializer(user).data,
                    message=f'Role {role_id} revoked from user {user.username}'
                )
        except Role.DoesNotExist:
            logger.warning(f"Role not found: {role_id}")
            raise NotFound(f"Role '{role_id}' not found.")
        except Exception as e:
            logger.error(f"Error revoking role: {str(e)}")
            return StandardResponse.error(str(e))
        
    @action(detail=True, methods=['get'])
    def permissions(self, request, pk=None):
        """Get all permissions for a specific user (both direct and from roles)."""
        user = self.get_object()
        
        # Get all permission IDs (from both direct permissions and roles)
        permission_ids = set()
        
        # Add direct permission IDs
        permission_ids.update(user.user_permissions.values_list('id', flat=True))
        
        # Add role permission IDs
        role_permission_ids = Permission.objects.filter(
            roles__in=user.roles.all()
        ).values_list('id', flat=True)
        permission_ids.update(role_permission_ids)
        
        # Fetch all permissions at once
        all_permissions = Permission.objects.filter(id__in=permission_ids)
        
        serializer = PermissionSerializer(all_permissions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def assign_permission(self, request, pk=None):
        """Assign a direct permission to a user."""
        user = self.get_object()
        permission_id = request.data.get('permission_id')
        
        try:
            permission = Permission.objects.get(id=permission_id)
            user.user_permissions.add(permission)
            return Response({'message': 'Permission assigned successfully'})
        except Permission.DoesNotExist:
            return Response(
                {'error': 'Permission not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['delete'], url_path='permissions/(?P<permission_id>\d+)')
    def revoke_permission(self, request, pk=None, permission_id=None):
        """Revoke a direct permission from a user."""
        user = self.get_object()
        
        try:
            permission = Permission.objects.get(id=permission_id)
            user.user_permissions.remove(permission)
            return Response({'message': 'Permission revoked successfully'})
        except Permission.DoesNotExist:
            return Response(
                {'error': 'Permission not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['get'])
    def direct_permissions(self, request, pk=None):
        """Get only direct permissions for a user (excluding role permissions)."""
        user = self.get_object()
        permissions = user.user_permissions.all()
        
        AdminLog.objects.create(
            user=request.user,
            action='view',
            module='user',
            details={
                'user_id': str(user.id),
                'username': user.username
            },
            status='success'
        )
        
        serializer = PermissionSerializer(permissions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def role_permissions(self, request, pk=None):
        """Get only permissions from user's roles."""
        user = self.get_object()
        permissions = Permission.objects.filter(roles__in=user.roles.all()).distinct()
        
        AdminLog.objects.create(
            user=request.user,
            action='view',
            module='user',
            details={
                'user_id': str(user.id),
                'username': user.username
            },
            status='success'
        )
        
        serializer = PermissionSerializer(permissions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['put', 'patch'], url_path='department')
    def department(self, request, pk=None):
        """
        Assign or update a user's department.
        """
        
        try:
            user = self.get_object()
            department_code = request.data.get('department_code')
            
            if not department_code:
                return StandardResponse.error(
                    "Department code is required", 
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            try:
                department = Department.objects.get(code=department_code)
            except Department.DoesNotExist:
                return StandardResponse.error(
                    "Department not found", 
                    status_code=status.HTTP_404_NOT_FOUND
                )

            # Update user's department
            user.department = department
            user.save()

            # Log the change
            AuditLog.objects.create(
                user=request.user,
                action='update',
                module='user',
                details={
                    'user_id': str(user.id),
                    'department_id': str(department.id),
                    'department_name': department.name
                },
                status='success'
            )

            serializer = self.get_serializer(user)
            return StandardResponse.success(
                data=serializer.data,
                message=f"Department updated successfully for user {user.username}"
            )

        except Exception as e:
            logger.error(f"Error updating department: {str(e)}")
            return StandardResponse.error(
                str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
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
        

class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        try:
            user = CustomUser.objects.get(email=email)
            reset_token = user.generate_reset_token()  # Assume this method generates a unique token
            reset_url = f"{request.build_absolute_uri('/user/reset-password/')}{reset_token}"

            send_mail(
                "Password Reset Request",
                f"Use this link to reset your password: {reset_url}",
                "noreply@yourdomain.com",
                [email],
            )
            logger.info(f"Password reset email sent to {email}.")
            return StandardResponse.success(message="Password reset email sent")
        except CustomUser.DoesNotExist:
            logger.warning(f"Password reset requested for non-existent email: {email}")
            return StandardResponse.error("User with this email does not exist", status.HTTP_404_NOT_FOUND)
        
        
class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        token = request.data.get("token")
        new_password = request.data.get("new_password")
        try:
            user = CustomUser.verify_reset_token(token)  # Assume this method validates the token and returns the user
            user.set_password(new_password)
            user.save()

            logger.info(f"Password reset successfully for {user.email}.")
            return StandardResponse.success(message="Password reset successfully")
        except ValidationError as e:
            logger.error(f"Password reset failed: {str(e)}")
            return StandardResponse.error(str(e), status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        current_password = request.data.get("current_password")
        new_password = request.data.get("new_password")
        user = request.user

        if not user.check_password(current_password):
            return StandardResponse.error("Current password is incorrect", status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        logger.info(f"Password changed successfully for {user.username}.")
        return StandardResponse.success(message="Password changed successfully")

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [HasPermission]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name']
    



class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['action', 'module', 'status']
    search_fields = ['user__email', 'user__username', 'details']
    ordering_fields = ['created_at', 'action', 'module']

    def get_queryset(self):
        queryset = AuditLog.objects.all()
        
        # Apply filters
        days = self.request.query_params.get('days', 7)
        activity_type = self.request.query_params.get('type', 'all')
        start_date = timezone.now() - timedelta(days=int(days))
        
        queryset = queryset.filter(created_at__gte=start_date)
        
        if activity_type != 'all':
            queryset = queryset.filter(module=activity_type)
            
        return queryset.select_related('user')
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'data': serializer.data
        })

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'status': 'success',
            'data': serializer.data
        })
    

    @action(detail=False, methods=['get'])
    def export(self, request):
        queryset = self.get_queryset()
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="audit_logs.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Timestamp',
            'User',
            'Action',
            'Module',
            'Details',
            'IP Address',
            'Status'
        ])
        
        for log in queryset:
            writer.writerow([
                log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                str(log.user) if log.user else 'System',
                log.get_action_display(),
                log.module,
                str(log.details) if log.details else '',
                log.ip_address or '',
                log.status
            ])
        
        return response

    @action(detail=False, methods=['get'])
    def summary(self, request):
        days = int(request.query_params.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)
        
        queryset = self.get_queryset().filter(created_at__gte=start_date)
        
        summary = {
            'total_actions': queryset.count(),
            'actions_by_type': queryset.values('action').annotate(
                count=Count('id')
            ),
            'actions_by_module': queryset.values('module').annotate(
                count=Count('id')
            ),
            'actions_by_status': queryset.values('status').annotate(
                count=Count('id')
            ),
            'top_users': queryset.values(
                'user__email'
            ).annotate(
                count=Count('id')
            ).order_by('-count')[:5]
        }
        
        return Response(summary)