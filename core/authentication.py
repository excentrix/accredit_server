from rest_framework_simplejwt.authentication import JWTAuthentication
from datetime import timedelta
from django.conf import settings

class CustomJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        # Add any custom validation here if needed
        return user