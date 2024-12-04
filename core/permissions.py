# core/permissions.py
from user_management.models import CustomUser
from rest_framework import permissions

class IsFaculty(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.has_role('faculty')

class IsIQACDirector(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.has_role('iqac_director')

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.has_role('admin')