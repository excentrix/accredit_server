# core/middleware.py
import logging
import traceback
from django.http import JsonResponse
from rest_framework import status

logger = logging.getLogger(__name__)

class ExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        logger.error(f"Unhandled exception: {str(exception)}")
        logger.error(traceback.format_exc())

        return JsonResponse({
            'error': 'Internal server error',
            'detail': str(exception) if settings.DEBUG else 'Please try again later'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith('/static/'):
            logger.info(f"Request: {request.method} {request.path}")
        
        response = self.get_response(request)
        
        if not request.path.startswith('/static/'):
            logger.info(f"Response: {response.status_code}")
        
        return response