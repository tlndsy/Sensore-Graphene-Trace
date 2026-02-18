from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required

from user.models import User, Message

# Create your views here.
@login_required(login_url='/user/home/')
def home(request):
    user = request.user
    notifications = len(Message.objects.filter(recipient=user, read_receipt=False))


    return render(request,'patient/home.html', {"user": user, "notifications": notifications})

def stats(request):
    return HttpResponse("This is the patients stats page (e.g., graph, heatmap")

def temp_logout(request):
    if request.method == 'POST':
        logout(request)
        return redirect("user:home")