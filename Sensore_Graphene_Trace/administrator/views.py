from django.apps import apps
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.forms import modelform_factory
from django.urls import reverse_lazy
from django.views.generic import ListView, UpdateView, CreateView, TemplateView, DeleteView
from django.db.models import Q
from django.db.models.fields.related import ForeignKey

from .mixins import BaseGenericModelMixin, BaseAdminMixin


class AdminHomeView(BaseAdminMixin, TemplateView):
    template_name = "administrator/administrator_home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        models_data = []

        for model in apps.get_models():
            app_label = model._meta.app_label

            if app_label not in self.allowed_apps:
                continue

            model_name = model._meta.model_name
            verbose_name = model._meta.verbose_name_plural.title()

            models_data.append({
                "name": verbose_name,
                "app_label": app_label,
                "model_name": model_name,
            })

        context["models"] = models_data
        return context


class GenericListView(BaseGenericModelMixin, ListView):
    template_name = "administrator/generic_list.html"
    context_object_name = "objects"
    paginate_by = 25
    permission_action = "view"

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

    def get_form_class(self):
        return modelform_factory(self.model, exclude=["password"])

    def get_success_url(self):
        return reverse_lazy(
            "user:administrator:generic_list",
            args=[self.model._meta.app_label, self.model._meta.model_name],
        )


class AdminPasswordChangeView(PasswordChangeView):
    form_class = AdminPasswordChangeForm
    template_name = "administrator/administrator_change_password.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_pk'] = self.kwargs.get('pk')
        return context

    def get_success_url(self):
        return reverse_lazy(
            "user:administrator:generic_update",
            args=[
                'user',
                'user',
                self.kwargs.get('pk'),
            ],
        )


class GenericDeleteView(DeleteView):
    template_name = "administrator/generic_delete.html"
    permission_action = "delete"

    def get_success_url(self):
        return reverse_lazy(
            "user:administrator:generic_list",
            args=[self.model._meta.app_label, self.model._meta.model_name],
        )
