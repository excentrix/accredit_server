# user_management/permissions.py
from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_role('admin')

class IsFaculty(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_role('faculty')

class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_role('student')

class HasPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Determine the resource and action from the request
        action = request.method.lower()
        resource = view.basename if hasattr(view, 'basename') else view.__class__.__name__.lower()
        
        return request.user.has_permission(resource, action)

class HasDynamicPermission(BasePermission):
    def has_permission(self, request, view):
        # Get resource and action from the view
        resource = getattr(view, 'resource', None)
        action = getattr(view, 'action', None)
        if not resource or not action:
            return False

        # Check if user has the required permission
        if request.user.is_authenticated:
            return request.user.has_permission(resource, action)
        return False
