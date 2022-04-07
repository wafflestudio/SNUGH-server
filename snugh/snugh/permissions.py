from rest_framework import permissions

class IsOwnerOrCreateReadOnly(permissions.BasePermission):
    """
    Only object's owner can update / delete object.
    Not owner but Authenticated user can create / get objects.  
    """
    message = '권한이 없습니다.'
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if hasattr(obj, 'plan'):
            return obj.plan.user == request.user
        elif hasattr(obj, 'semester'):
            return obj.semester.plan.user == request.user
        return obj.user == request.user