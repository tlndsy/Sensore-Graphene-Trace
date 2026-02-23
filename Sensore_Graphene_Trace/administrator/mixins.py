from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class GroupRequiredMixin(UserPassesTestMixin):
    group_required = None  # string or list of group names

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

    def handle_no_permission(self):
        raise PermissionDenied("You do not have permission to access this page.")