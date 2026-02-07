from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, HttpResponse, redirect


# Create your views here.
def home(request):
    """if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            print("Login success")"""
    form = AuthenticationForm(request=request)
    return render(request, "home.html", {"form":form})

def register(request):
    return render(request, "register.html", {})
