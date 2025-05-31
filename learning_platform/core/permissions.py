from rest_framework.permissions import BasePermission


class IsInstructor(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "instructor"


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "admin"


class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "student"
