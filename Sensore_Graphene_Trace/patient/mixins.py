from Sensore_Graphene_Trace import global_constants as constants
from user.mixins import GroupRequiredMixin
from user.utils import notifications


class BasePatientMixin(GroupRequiredMixin):
    """
    Base patient access rules shared by all patient views.
    """

    # Login redirects
    login_url = "user:home"
    redirect_field_name = "next"

    # restrict which user groups can access
    group_required = [constants.PATIENT, constants.ADMIN]

    # restrict which apps are allowed
    allowed_apps = ["user"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["num_notifications"] = notifications.get_notification_count(self.request.user)

        return context