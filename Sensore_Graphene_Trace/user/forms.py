from datetime import datetime

from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm
from django.utils.html import avoid_wrapping

from .models import User
from django import forms

class RegisterForm(UserCreationForm):
    email = forms.EmailField(max_length=255, required=True)
    first_name = forms.CharField(max_length=255, required=True)
    last_name = forms.CharField(max_length=255, required=True)
    phone_number = forms.CharField(max_length=255)
    date_of_birth = forms.DateField(required=True, widget=forms.SelectDateWidget(
        years=range(1900, datetime.now().year + 1), attrs={'class': 'field'}
    ))

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone_number', 'date_of_birth')

class LoginForm(AuthenticationForm):
    username = forms.EmailField(label ="Email", max_length=255, required=True)

    class Meta:
        model = User
        fields = ('email',)
