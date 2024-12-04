import uuid
import time
import logging
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
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
        if request.path.startswith('/admin/') or request.method == 'OPTIONS':
            return None

        EXEMPT_PATHS = [
            '/api/token/',
            '/api/token/refresh/',
            '/api/register/',
            '/health/',
            '/api/schema/',
            '/api/schema/swagger-ui/',
            '/api/schema/redoc/'
        ]
        
        if request.path in EXEMPT_PATHS:
            return None

        # Rate limiting check
        ip = self.get_client_ip(request)
        if self.is_rate_limited(ip):
            logger.warning(f'Rate limit exceeded for IP: {ip}')
            return JsonResponse({
                'error': 'Rate limit exceeded'
            }, status=429)

        try:
            auth_header = request.headers.get('Authorization', '')
            if not auth_header:
                return JsonResponse({
                    'error': 'No authorization token provided'
                }, status=401)

            token = auth_header.split(' ')[1]
            
            # Check token blacklist
            if self.is_token_blacklisted(token):
                return JsonResponse({
                    'error': 'Token has been blacklisted'
                }, status=401)

            validated_token = self.jwt_auth.get_validated_token(token)
            request.user = self.jwt_auth.get_user(validated_token)[0]

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

        if not request.user.is_authenticated:
            return JsonResponse({
                'error': 'Unauthorized access'
            }, status=401)

        action = request.method.lower()
        path_parts = request.path.strip('/').split('/')
        resource = path_parts[1] if len(path_parts) > 1 else None

        if not resource:
            return JsonResponse({
                'error': 'Invalid resource path'
            }, status=400)

        if not request.user.has_permission(resource, action):
            logger.warning(
                f"Permission denied for user {request.user.email} "
                f"accessing {resource} with action {action}"
            )
            return JsonResponse({
                'error': 'Permission denied',
                'detail': f'You do not have permission to perform {action} on {resource}'
            }, status=403)

        return None

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')

    def is_rate_limited(self, ip):
        cache_key = f'rate_limit_{ip}'
        requests = cache.get(cache_key, 0)
        if requests >= 1000:  # Limit per minute
            return True
        cache.set(cache_key, requests + 1, 60)  # 60 seconds expiry
        return False

    def is_token_blacklisted(self, token):
        return cache.get(f'blacklist_token_{token}')
