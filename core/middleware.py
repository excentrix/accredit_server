# core/middleware.py
from django.http import JsonResponse
from rest_framework import status

class APIErrorHandlerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        if request.path.startswith('/api/'):
            return JsonResponse({
                'error': str(exception),
                'detail': getattr(exception, 'detail', str(exception))
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return None