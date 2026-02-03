from django.shortcuts import render, HttpResponse

# Create your views here.
def home(request):
    return HttpResponse("This is the home page/login screen")

def register(request):
    return HttpResponse("This is the registration page")