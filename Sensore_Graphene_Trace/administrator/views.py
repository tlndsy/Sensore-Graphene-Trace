from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

from . import forms
from user.models import Message

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
        form = forms.AdminUserCreationForm(request.POST)
        if form.is_valid():
            new_user = form.save(commit=True)
            return redirect('user:administrator')
    else:
        form = forms.AdminUserCreationForm()

    # Get number of notifications for the user
    num_notifications = len(Message.objects.filter(recipient=user, read_receipt=False))

    context = {"form": form, "user": user, "num_notifications": num_notifications}
    return render(request, 'administrator/userCreation.html', context)