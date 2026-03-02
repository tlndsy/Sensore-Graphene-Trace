from django.apps import apps
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import modelform_factory
from django.http import Http404
from django.urls import reverse_lazy, reverse, NoReverseMatch
from django.views.generic import ListView, UpdateView, CreateView, TemplateView, DeleteView
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.db.models.fields.related import ForeignKey

from user.mixins import GroupRequiredMixin

import Sensore_Graphene_Trace.global_constants as constants


class AdminHomeView(LoginRequiredMixin, GroupRequiredMixin, TemplateView):
    template_name = "administrator/home.html"

    group_required = [constants.ADMIN]


    def get_context_data(self, **kwargs):

        ALLOWED_APPS = ["user"]

        def safe_reverse(name, *args):
            try:
                return reverse(name, args=args)
            except NoReverseMatch:
                return None

        context = super().get_context_data(**kwargs)
        models_data = []

        for model in apps.get_models():
            app_label = model._meta.app_label

            if app_label not in ALLOWED_APPS:
                continue

            model_name = model._meta.model_name
            verbose_name = model._meta.verbose_name_plural.title()

            models_data.append({
                "name": verbose_name,
                "list_url": safe_reverse(f"{app_label}:{model_name}_list"),
                "create_url": reverse("user:administrator:generic_create", args=[app_label, model_name]),
                "update_url": safe_reverse(f"{app_label}:{model_name}_update", 1),
                "delete_url": safe_reverse(f"{app_label}:{model_name}_delete", 1),
                "app_label": app_label,
                "model_name": model_name,
            })

        context["models"] = models_data
        return context


class BaseGenericModelMixin(LoginRequiredMixin, GroupRequiredMixin):
    """
    Shared logic for generic CRUD views.
    """

    # "add", "change", "delete", "view"
    permission_action = None

    # restrict which apps are allowed
    allowed_apps = ["user"]

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

    def check_permissions(self):
        if not self.permission_action:
            return

        perm = f"{self.model._meta.app_label}.{self.permission_action}_{self.model._meta.model_name}"
        if not self.request.user.has_perm(perm):
            raise PermissionDenied

    def dispatch(self, request, *args, **kwargs):
        self.model = self.get_model()
        self.check_permissions()
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.model.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_verbose_name"] = self.model._meta.verbose_name.title()
        context["app_label"] = self.model._meta.app_label
        context["model_name"] = self.model._meta.model_name
        return context


class GenericListView(BaseGenericModelMixin, ListView):
    template_name = "administrator/generic_list.html"
    context_object_name = "objects"
    paginate_by = 25
    permission_action = "view"
    group_required = [constants.ADMIN]

    SEARCH_FIELD_TYPES = ("CharField", "TextField", "EmailField")


    # Override to add searching, filtering, and sorting based on query parameters
    def get_queryset(self):
        qs = super().get_queryset()
        request = self.request

        # SEARCHING
        query = request.GET.get("q")
        if query:
            search_q = Q()
            for field in self.model._meta.fields:
                if field.get_internal_type() in self.SEARCH_FIELD_TYPES:
                    search_q |= Q(**{f"{field.name}__icontains": query})
            qs = qs.filter(search_q)

        # FILTERING
        for field in self.model._meta.fields:
            value = request.GET.get(field.name)
            if value:
                qs = qs.filter(**{field.name: value})

        # SORTING
        sort = request.GET.get("sort")
        field_names = [f.name for f in self.model._meta.fields]

        if sort:
            sort_field = sort.lstrip("-")
            if sort_field in field_names:
                qs = qs.order_by(sort)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        fields = self.model._meta.fields
        filters = []

        for field in fields:
            if isinstance(field, ForeignKey):
                related_model = field.remote_field.model
                filters.append({
                    "name": field.name,
                    "label": field.verbose_name,
                    "type": "fk",
                    "choices": related_model.objects.all(),
                    "value": self.request.GET.get(field.name, ""),
                })
            else:
                filters.append({
                    "name": field.name,
                    "label": field.verbose_name,
                    "type": "text",
                    "value": self.request.GET.get(field.name, ""),
                })

        context["fields"] = fields
        context["filters"] = filters
        context["search_query"] = self.request.GET.get("q", "")
        context["current_sort"] = self.request.GET.get("sort", "")
        context["querystring"] = self.request.GET.urlencode()

        return context


class GenericCreateView(BaseGenericModelMixin, CreateView):
    template_name = "administrator/generic_create.html"
    permission_action = "add"
    group_required = [constants.ADMIN]

    def get_form_class(self):
        return modelform_factory(self.model, fields="__all__")

    def get_success_url(self):
        return reverse_lazy(
            "user:administrator:generic_list",
            args=[self.model._meta.app_label, self.model._meta.model_name],
        )

class GenericUpdateView(BaseGenericModelMixin, UpdateView):
    template_name = "administrator/generic_update.html"
    permission_action = "change"
    group_required = [constants.ADMIN]

    def get_form_class(self):
        return modelform_factory(self.model, fields="__all__")

    def get_success_url(self):
        return reverse_lazy(
            "user:administrator:generic_list",
            args=[self.model._meta.app_label, self.model._meta.model_name],
        )

class GenericDeleteView(BaseGenericModelMixin, DeleteView):
    template_name = "administrator/generic_delete.html"
    permission_action = "delete"
    group_required = [constants.ADMIN]

    def get_success_url(self):
        return reverse_lazy(
            "user:administrator:generic_list",
            args=[self.model._meta.app_label, self.model._meta.model_name],
        )

