from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class GroupRequiredMixin(UserPassesTestMixin):
    group_required = None

    # Override the test_func method to check if the user belongs to the required group(s)
    def test_func(self):
        user = self.request.user

        if not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        if isinstance(self.group_required, str):
            groups = [self.group_required]
        else:
            groups = self.group_required

        return user.groups.filter(name__in=groups).exists()

    # Raise 403 Forbidden if the user does not have permission to access the page
    def handle_no_permission(self):
        # if user is not logged in, redirect to login page
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()

        raise PermissionDenied("You do not have permission to access this page.")