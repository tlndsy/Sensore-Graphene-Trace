from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, HttpResponse, redirect
from .forms import RegisterForm, LoginForm


# Create your views here.
def home(request):
    login_form = LoginForm()
    register_form = RegisterForm()
    if request.method == 'POST':
        if request.POST.get("form_type") == "login":
            login_form =LoginForm(request, data=request.POST)
            if login_form.is_valid():
                print("Login success")
                login(request, login_form.get_user())
                return redirect('user:patient:home')

        elif request.POST.get("form_type") == "register":
            register_form = RegisterForm(request.POST)
            if register_form.is_valid():
                user = register_form.save()
                print("Registration success")
                return redirect('home')
            else:
                print("Registration failed")

    return render(request, "home.html", {"form":login_form, "register_form":register_form})

def logout_view(request):
    logout(request)
    return redirect('home')