# core/middleware/error_handler.py
import logging
import traceback
from django.http import JsonResponse
from rest_framework import status
from django.core.exceptions import ValidationError
from rest_framework.exceptions import APIException
from django.db import DatabaseError
from redis.exceptions import RedisError
from django.conf import settings

logger = logging.getLogger(__name__)

class GlobalErrorHandler:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            return self.handle_error(e)

    def handle_error(self, exc):
        """Handle different types of exceptions and return appropriate responses"""
        
        # Get full traceback
        trace = traceback.format_exc()
        
        # Log the error with traceback
        logger.error(f"Unhandled exception: {str(exc)}\n{trace}")
        
        # Define error response structure
        error_response = {
            'status': 'error',
            'message': str(exc),
        }

        # Add debug information if DEBUG is True
        if settings.DEBUG:
            error_response['debug'] = {
                'exception_type': exc.__class__.__name__,
                'traceback': trace
            }

        # Handle specific exceptions
        if isinstance(exc, ValidationError):
            error_response['type'] = 'validation_error'
            error_response['errors'] = exc.message_dict if hasattr(exc, 'message_dict') else exc.messages
            return JsonResponse(error_response, status=status.HTTP_400_BAD_REQUEST)

        elif isinstance(exc, APIException):
            error_response['type'] = 'api_error'
            return JsonResponse(error_response, status=exc.status_code)

        elif isinstance(exc, DatabaseError):
            error_response['type'] = 'database_error'
            error_response['message'] = "A database error occurred"
            return JsonResponse(error_response, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        elif isinstance(exc, RedisError):
            error_response['type'] = 'cache_error'
            error_response['message'] = "A caching error occurred"
            return JsonResponse(error_response, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        elif isinstance(exc, PermissionError):
            error_response['type'] = 'permission_error'
            return JsonResponse(error_response, status=status.HTTP_403_FORBIDDEN)

        # Default server error response
        error_response['type'] = 'server_error'
        return JsonResponse(error_response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)