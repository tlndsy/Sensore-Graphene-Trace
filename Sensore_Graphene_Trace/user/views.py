from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, HttpResponse, redirect
from .forms import RegisterForm, LoginForm


# Create your views here.
def home(request):

    login_form = LoginForm(request)
    register_form = RegisterForm()
    if request.method == 'POST':

        if request.POST.get("form_type") == "login":
            login_form = AuthenticationForm(request, data=request.POST)
            if login_form.is_valid():
                login(request, login_form.get_user())
                print("Login success") # Will adapt when the home page exists

        if request.POST.get("form_type") == "register":
            register_form = UserCreationForm(request.POST)
            if register_form.is_valid():
                user = register_form.save()
                print("Registration success")
                return redirect('home')

    return render(request, "home.html", {"form":login_form, "register_form":register_form})

def register(request):
    return render(request, "register.html", {})
