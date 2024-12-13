import uuid
import time
import logging
from django.http import JsonResponse
import json
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.core.cache import cache

logger = logging.getLogger(__name__)

class RequestIDMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request_id = str(uuid.uuid4())
        request.id = request_id
        logger.debug(f'Request ID: {request_id}')

class PerformanceMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.start_time = time.time()

    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            response['X-Page-Generation-Duration-ms'] = int(duration * 1000)
            logger.info(f'Request {request.id} took {duration:.2f}s')
        return response

class RBACMiddleware(MiddlewareMixin):
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.jwt_auth = JWTAuthentication()

    def process_request(self, request):
        # Define exempt paths
        EXEMPT_PATHS = [
            '/admin/',
            '/user/token/',
            '/user/token/refresh/',
            '/user/register/',
            '/user/logout/',
            '/user/reset-password-request/',
            '/user/reset-password/',
            '/user/users/me/',
            '/health/',
            '/swagger/',
            '/redoc/',
            '/static/',
            '/media/',
            '/api/schema/',
        ]

        # Check if path starts with any exempt path
        current_path = request.path.rstrip('/')
        if any(current_path.startswith(path.rstrip('/')) for path in EXEMPT_PATHS):
            return None

        # Skip OPTIONS requests
        if request.method == 'OPTIONS':
            return None

        try:
            # Get and validate token
            auth_header = request.headers.get('Authorization', '')
            if not auth_header:
                return JsonResponse({
                    'error': 'No authorization token provided'
                }, status=401)

            try:
                token_type, token = auth_header.split(' ')
                if token_type.lower() != 'bearer':
                    raise ValueError('Invalid token type')
            except ValueError:
                return JsonResponse({
                    'error': 'Invalid authorization header format'
                }, status=401)

            # Authenticate user
            authenticated = self.jwt_auth.authenticate(request)
            if authenticated is None:
                return JsonResponse({
                    'error': 'Invalid authentication token'
                }, status=401)

            request.user = authenticated[0]

            # Skip permission check for superusers
            if request.user.is_superuser:
                return None

            # Get action and resource from path
            action = self.get_action_from_method(request.method)
            resource = self.get_resource_from_path(request.path)

            if not self.check_user_permission(request.user, resource, action):
                logger.warning(
                    f"Permission denied for user {request.user.email} "
                    f"accessing {resource} with action {action}"
                )
                return JsonResponse({
                    'error': 'Permission denied',
                    'detail': f'You do not have permission to perform {action} on {resource}'
                }, status=403)

        except (InvalidToken, TokenError) as e:
            logger.warning(f"Invalid token error: {str(e)}")
            return JsonResponse({
                'error': 'Invalid authentication token'
            }, status=401)
        except Exception as e:
            logger.error(f"Unexpected error in RBAC middleware: {str(e)}")
            return JsonResponse({
                'error': 'Internal server error'
            }, status=500)

        return None

    def get_resource_from_path(self, path):
        """Extract resource from path"""
        parts = [p for p in path.strip('/').split('/') if p]
        
        # Handle API paths
        if parts and parts[0] == 'api':
            parts.pop(0)  # Remove 'api' prefix
        
        # Map URL patterns to resources
        if parts:
            resource_mapping = {
                'academic-years': 'academic_year',
                'submissions': 'submission',
                'criteria': 'criteria',
                'dashboard': 'dashboard',
                'boards': 'board',
                'templates': 'template',
                'users': 'user',
                'roles': 'role',
                'permissions': 'permission',
                'departments': 'department',
                'audit-logs': 'audit_log'
            }
            return resource_mapping.get(parts[0], parts[0])
        return None

    def get_action_from_method(self, method):
        """Map HTTP method to action"""
        method_mapping = {
            'GET': 'view',
            'POST': 'create',
            'PUT': 'update',
            'PATCH': 'update',
            'DELETE': 'delete'
        }
        return method_mapping.get(method.upper(), 'other')

    def check_user_permission(self, user, resource, action):
        """Check if user has permission for the resource and action"""
        try:
            # Debug logging
            logger.debug(f"Checking permission for user {user.email} on {resource}.{action}")
            
            # Skip for superuser
            if user.is_superuser:
                return True

            # Check user roles and permissions
            user_roles = user.roles.all() if hasattr(user, 'roles') else []
            
            # Log roles for debugging
            logger.debug(f"User roles: {[role.name for role in user_roles]}")
            
            # Check permissions through roles
            for role in user_roles:
                if role.has_permission(resource, action):
                    logger.debug(f"Permission granted through role: {role.name}")
                    return True

            logger.debug("Permission denied")
            return False
            
        except Exception as e:
            logger.error(f"Error checking permissions: {str(e)}")
            return False

class AuditLogMiddleware(MiddlewareMixin):
    EXEMPT_PATHS = {'/admin/', '/static/', '/media/', '/favicon.ico'}
    EXEMPT_STATUS_CODES = {304, 404, 403}
    
    def should_audit(self, request, response=None):
        """Determine if the request should be audited"""
        # Check if path starts with any exempt paths
        if any(request.path.startswith(path) for path in self.EXEMPT_PATHS):
            return False
            
        # Skip OPTIONS requests
        if request.method == 'OPTIONS':
            return False
            
        # Skip exempt status codes if response is provided
        if response and response.status_code in self.EXEMPT_STATUS_CODES:
            return False
            
        # Skip if user is not authenticated
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return False
            
        return True

    def process_request(self, request):
        """Process the request before the view is called"""
        if not self.should_audit(request):
            return None

        # Store request info for later use
        request.audit_data = {
            'ip_address': self.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT'),
            'method': request.method,
            'path': request.path,
            'query_params': dict(request.GET.items()),
            'body': self.get_request_body(request),
            'start_time': timezone.now(),
        }

    def process_response(self, request, response):
        """Process the response after the view is called"""
        if not hasattr(request, 'audit_data') or not self.should_audit(request, response):
            return response

        try:
            from .models import AuditLog
            
            # Get the module from the path
            path_parts = [p for p in request.path.strip('/').split('/') if p]
            module = path_parts[0] if path_parts else 'root'

            # Get additional data that might have been added by the view
            extra_details = getattr(request, 'audit_extra_details', {})

            # Prepare details
            details = {
                'path': request.path,
                'method': request.method,
                'status_code': response.status_code,
                'query_params': request.audit_data.get('query_params'),
                **extra_details  # Merge any extra details added by views
            }

            # Create audit log entry
            AuditLog.objects.create(
                user=request.user,
                action=self._get_action(request.method),
                module=module,
                details=details,
                ip_address=request.audit_data.get('ip_address'),
                user_agent=request.audit_data.get('user_agent'),
                status='success' if response.status_code < 400 else 'failure'
            )

        except Exception as e:
            logger.error(f"Error creating audit log: {str(e)}", exc_info=True)

        return response

    def get_request_body(self, request):
        """Safely get request body"""
        try:
            if request.content_type == 'application/json':
                return json.loads(request.body.decode('utf-8'))
            return dict(request.POST.items())
        except:
            return {}

    def _get_action(self, method):
        """Map HTTP method to audit action"""
        return {
            'GET': 'view',
            'POST': 'create',
            'PUT': 'update',
            'PATCH': 'update',
            'DELETE': 'delete'
        }.get(method, 'other')

    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')