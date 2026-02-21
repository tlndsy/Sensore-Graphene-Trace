from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

from user.models import User, Message, PressureMapReading, ReadingEquipment
from . import forms


# Create your views here.
@login_required(login_url='/user/home/')
def home(request):
    user = request.user
    # Check if the user belongs to the 'Patient' group
    if not user.groups.filter(name='Patient').exists():
        return HttpResponseForbidden("403 Forbidden: You do not have permission to access this page.")

    # Get number of notifications for the user
    num_notifications = len(Message.objects.filter(recipient=user, read_receipt=False))

    context = {"user": user, "notifications": num_notifications}

    return render(request,'patient/home.html', context)


@login_required(login_url='/user/home/')
def viewDevices(request):
    user = request.user
    if not user.groups.filter(name='Patient').exists():
        return HttpResponseForbidden("403 Forbidden: You do not have permission to access this page.")

    # Get number of notifications for the user
    num_notifications = len(Message.objects.filter(recipient=user, read_receipt=False))

    devices = ReadingEquipment.objects.filter(user=user)
    context = {"devices": devices, "num_notifications": num_notifications}
    return render(request, 'patient/viewDevices.html', context)

@login_required(login_url='/user/home/')
def registerDevice(request):
    user = request.user
    if not user.groups.filter(name='Patient').exists():
        return HttpResponseForbidden("403 Forbidden: You do not have permission to access this page.")

    if request.method == 'POST':
        form = forms.RegisterDevice(request.POST, request.FILES)
        if form.is_valid():
            new_device = form.save(commit=False)
            new_device.user = user
            new_device.save()
            return redirect('user:patient:viewDevices')
    else:
        form = forms.RegisterDevice()

    num_notifications = len(Message.objects.filter(recipient=user, read_receipt=False))
    context = {"form": form, "user": user, "num_notifications": num_notifications}
    return render(request, 'patient/registerDevice.html', context)

def stats(request):
    return HttpResponse("This is the patients stats page (e.g., graph, heatmap")

def profile(request):
    return HttpResponse("This is the patients profile page")

def notifications(request):
    return HttpResponse("This is the patients notification page")

def messages(request):
    return HttpResponse("This is the patients messaging page")


def temp_logout(request):
    if request.method == 'POST':
        logout(request)
        return redirect("user:home")