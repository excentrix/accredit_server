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

        # Determine the action based on HTTP method
        method_to_action_map = {
            'GET': 'view',
            'POST': 'create',
            'PUT': 'update',
            'PATCH': 'update',
            'DELETE': 'delete'
        }
        action = method_to_action_map.get(request.method.upper(), None)
        if not action:
            return False

        # Determine the resource from the view's queryset model
        if hasattr(view, 'get_queryset') and view.get_queryset() is not None:
            resource = view.get_queryset().model.__name__.lower()
        elif hasattr(view, 'queryset') and view.queryset is not None:
            resource = view.queryset.model.__name__.lower()
        else:
            resource = view.__class__.__name__.lower()
            
        print(request.user.has_permission(resource, action))


        return request.user.has_permission(resource, action)

class HasDynamicPermission(BasePermission):
    def has_permission(self, request, view):
        # Get resource and action from the view
        resource = getattr(view, 'resource', None)
        action = getattr(view, 'action', None)

        if not resource or not action:
            # Default fallback to determine action
            action = request.method.lower()
            if hasattr(view, 'queryset') and view.queryset is not None:
                resource = view.queryset.model.__name__.lower()
            else:
                resource = view.__class__.__name__.lower()

        # Check if user has the required permission
        if request.user.is_authenticated:
            return request.user.has_permission(resource, action)
        return False