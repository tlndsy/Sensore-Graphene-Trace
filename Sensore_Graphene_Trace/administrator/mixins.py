from django.apps import apps
from django.http import Http404

from user.mixins import GroupRequiredMixin


class BaseGenericModelMixin(GroupRequiredMixin):
    """
    Shared logic for generic CRUD views.
    """

    # "add", "change", "delete", "view"
    permission_action = None

    # restrict which apps are allowed
    allowed_apps = ["user"]

    # GroupRequiredMixin Overrides

    # Login redirects
    login_url = "user:home"
    redirect_field_name = "user:administrator"

    # restrict which user groups can access
    group_required = None

    def get_model(self):
        app_label = self.kwargs.get("app_label")
        model_name = self.kwargs.get("model_name")

        model = apps.get_model(app_label, model_name)
        if model is None:
            raise Http404("Model not found")

        if self.allowed_apps and model._meta.app_label not in self.allowed_apps:
            raise Http404("App not allowed")

        return model

    def dispatch(self, request, *args, **kwargs):
        self.model = self.get_model()
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        # Run GroupRequiredMixin
        if not super().test_func():
            return False

        # No permission requirement
        if not self.permission_action:
            return True

        perm = f"{self.model._meta.app_label}.{self.permission_action}_{self.model._meta.model_name}"
        return self.request.user.has_perm(perm)

    def get_queryset(self):
        return self.model.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_verbose_name"] = self.model._meta.verbose_name.title()
        context["app_label"] = self.model._meta.app_label
        context["model_name"] = self.model._meta.model_name
        return context