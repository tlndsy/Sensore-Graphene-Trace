from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

from user.models import User, Message, PressureMapReading, ReadingEquipment


# Create your views here.
@login_required(login_url='/user/home/')
def home(request):
    user = request.user
    # Check if the user belongs to the 'Patient' group
    if not user.groups.filter(name='Patient').exists():
        return HttpResponseForbidden("403 Forbidden: You do not have permission to access this page.")

    # Get number of notifications for the user
    notifications = len(Message.objects.filter(recipient=user, read_receipt=False))

    context = {"user": user, "notifications": notifications}

    return render(request,'patient/home.html', context)

def stats(request):
    return HttpResponse("This is the patients stats page (e.g., graph, heatmap")

def temp_logout(request):
    if request.method == 'POST':
        logout(request)
        return redirect("user:home")