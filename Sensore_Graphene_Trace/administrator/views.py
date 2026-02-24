from django.apps import apps
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import modelform_factory
from django.http import Http404
from django.urls import reverse_lazy, reverse, NoReverseMatch
from django.views.generic import ListView, UpdateView, CreateView, TemplateView, DeleteView

from .mixins import GroupRequiredMixin


class AdminHomeView(LoginRequiredMixin, GroupRequiredMixin, TemplateView):
    template_name = "administrator/home.html"

    group_required = ["Admin"]


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


class GenericCreateView(LoginRequiredMixin, GroupRequiredMixin, CreateView):
    template_name = "administrator/generic_create.html"

    group_required = ["Admin"]

    def dispatch(self, request, *args, **kwargs):
        self.model = self.get_model()
        self.form_class = modelform_factory(self.model, fields="__all__")
        return super().dispatch(request, *args, **kwargs)

    def get_model(self):
        app_label = self.kwargs.get("app_label")
        model_name = self.kwargs.get("model_name")

        model = apps.get_model(app_label, model_name)
        if model is None:
            raise Http404("Model not found")

        return model

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_verbose_name"] = self.model._meta.verbose_name.title()
        return context

    def get_success_url(self):
        return reverse_lazy("model_dashboard")

class GenericListView(LoginRequiredMixin, GroupRequiredMixin, ListView):
    template_name = "administrator/generic_list.html"
    context_object_name = "objects"
    paginate_by = 25

    group_required = ["Admin"]

    def dispatch(self, request, *args, **kwargs):
        self.model = self.get_model()
        return super().dispatch(request, *args, **kwargs)

    def get_model(self):
        app_label = self.kwargs.get("app_label")
        model_name = self.kwargs.get("model_name")

        model = apps.get_model(app_label, model_name)
        if model is None:
            raise Http404("Model not found")

        return model

    def get_queryset(self):
        return self.model.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_verbose_name"] = self.model._meta.verbose_name_plural.title()
        context["app_label"] = self.model._meta.app_label
        context["model_name"] = self.model._meta.model_name
        context["fields"] = self.model._meta.fields
        return context

class GenericUpdateView(LoginRequiredMixin, GroupRequiredMixin, UpdateView):
    template_name = "administrator/generic_update.html"

    group_required = ["Admin"]

    def dispatch(self, request, *args, **kwargs):
        self.model = self.get_model()

        self.form_class = modelform_factory(self.model, fields="__all__")
        return super().dispatch(request, *args, **kwargs)

    def get_model(self):
        app_label = self.kwargs.get("app_label")
        model_name = self.kwargs.get("model_name")

        model = apps.get_model(app_label, model_name)
        if model is None:
            raise Http404("Model not found")

        return model

    def get_queryset(self):
        return self.model.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_verbose_name"] = self.model._meta.verbose_name.title()
        context["app_label"] = self.model._meta.app_label
        context["model_name"] = self.model._meta.model_name
        return context

    def get_success_url(self):
        return reverse_lazy(
            "generic_list",
            args=[self.model._meta.app_label, self.model._meta.model_name],
        )

class GenericDeleteView(LoginRequiredMixin, GroupRequiredMixin, DeleteView):
    template_name = "administrator/generic_delete.html"

    def dispatch(self, request, *args, **kwargs):
        self.model = self.get_model()

        return super().dispatch(request, *args, **kwargs)

    def get_model(self):
        app_label = self.kwargs.get("app_label")
        model_name = self.kwargs.get("model_name")

        model = apps.get_model(app_label, model_name)
        if model is None:
            raise Http404("Model not found")

        return model

    def get_queryset(self):
        return self.model.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_verbose_name"] = self.model._meta.verbose_name.title()
        context["app_label"] = self.model._meta.app_label
        context["model_name"] = self.model._meta.model_name
        return context

    def get_success_url(self):
        return reverse_lazy(
            "generic_list",
            args=[self.model._meta.app_label, self.model._meta.model_name],
        )