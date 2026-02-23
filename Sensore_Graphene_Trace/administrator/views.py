from django.views.generic import ListView, UpdateView
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden

from django.urls import reverse_lazy

from user.models import Message, User
from .forms import AdminUserFilterForm, AdminUserCreationForm, AdminUserUpdateForm
from .mixins import GroupRequiredMixin


# Create your views here.
@login_required(login_url='/user/home/')
def home(request):
    user = request.user
    # Check if the user belongs to the 'Patient' group
    if not user.groups.filter(name='Admin').exists():
        return HttpResponseForbidden("403 Forbidden: You do not have permission to access this page.")

    # Get number of notifications for the user
    num_notifications = len(Message.objects.filter(recipient=user, read_receipt=False))

    context = {"user": user, "num_notifications": num_notifications}

    return render(request,'administrator/home.html', context)

@login_required(login_url='/user/home/')
def create_user(request):
    user = request.user
    if not user.groups.filter(name='Admin').exists():
        return HttpResponseForbidden("403 Forbidden: You do not have permission to access this page.")

    if request.method == 'POST':
        form = AdminUserCreationForm(request.POST)
        if form.is_valid():
            new_user = form.save(commit=True)
            return redirect('user:administrator')
    else:
        form = AdminUserCreationForm()

    # Get number of notifications for the user
    num_notifications = len(Message.objects.filter(recipient=user, read_receipt=False))

    context = {"form": form, "user": user, "num_notifications": num_notifications}
    return render(request, 'administrator/userCreation.html', context)


class AdminUserListView(LoginRequiredMixin,GroupRequiredMixin,ListView):
    model = User
    template_name = "administrator/user_list.html"
    context_object_name = "users"
    paginate_by = 20

    group_required = ['Admin']

    SORTABLE_FIELDS = {
        "email": "email",
        "first_name": "first_name",
        "last_name": "last_name",
        "role": "role",
        "is_active": "is_active",
        "date_joined": "date_joined",
    }

    def get_queryset(self):
        queryset = User.objects.all()
        self.form = AdminUserFilterForm(self.request.GET or None)

        if self.form.is_valid():
            cd = self.form.cleaned_data

            if cd.get("email"):
                queryset = queryset.filter(email__icontains=cd["email"])

            if cd.get("first_name"):
                queryset = queryset.filter(first_name__icontains=cd["first_name"])

            if cd.get("last_name"):
                queryset = queryset.filter(last_name__icontains=cd["last_name"])

            if cd.get("role"):
                queryset = queryset.filter(role=cd["role"])

            if cd.get("is_active") == "true":
                queryset = queryset.filter(is_active=True)
            elif cd.get("is_active") == "false":
                queryset = queryset.filter(is_active=False)

            if cd.get("joined_after"):
                queryset = queryset.filter(date_joined__gte=cd["joined_after"])

            if cd.get("joined_before"):
                queryset = queryset.filter(date_joined__lte=cd["joined_before"])

        sort = self.request.GET.get("sort")
        direction = self.request.GET.get("direction", "asc")

        if sort in self.SORTABLE_FIELDS:
            field = self.SORTABLE_FIELDS[sort]
            if direction == "desc":
                field = f"-{field}"
            queryset = queryset.order_by(field)
        else:
            queryset = queryset.order_by("-date_joined")  # default

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.form
        context["columns"] = [
            ("email", "Email"),
            ("first_name", "First Name"),
            ("last_name", "Last Name"),
            ("role", "Role"),
            ("is_active", "Active"),
            ("date_joined", "Date Joined"),
        ]
        context["current_sort"] = self.request.GET.get("sort", "")
        context["current_direction"] = self.request.GET.get("direction", "asc")
        return context

class AdminUserUpdateView(LoginRequiredMixin, GroupRequiredMixin, UpdateView):
    model = User
    form_class = AdminUserUpdateForm
    template_name = "administrator/user_edit.html"
    context_object_name = "edit_user"

    group_required = ["Admin"]

    def get_success_url(self):
        messages.success(self.request, "User updated successfully.")
        return reverse_lazy("user:administrator:admin_user_list")

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.is_superuser and not request.user.is_superuser:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("You cannot edit a superuser.")
        return super().dispatch(request, *args, **kwargs)