from rest_framework.permissions import BasePermission


class IsProjectOwner(BasePermission):
    """Allow access only to the project's owner."""
    message = "You do not have permission to modify this project."

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class CanDeleteTask(BasePermission):
    """Allow deletion only to task creator or project owner."""
    message = "Only the task creator or project owner can delete this task."

    def has_object_permission(self, request, view, obj):
        return (
            obj.created_by == request.user or
            obj.project.owner == request.user
        )