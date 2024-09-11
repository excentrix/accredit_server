from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NaacFileViewSet

router = DefaultRouter()
router.register(r'naac', NaacFileViewSet)

urlpatterns = [
    path('', include(router.urls)),
]