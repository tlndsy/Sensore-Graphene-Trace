from datetime import datetime

from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm
from django.core.exceptions import ValidationError
from django.utils.html import avoid_wrapping

from .models import User
from django import forms

# User registration form for patients
class RegisterForm(UserCreationForm):
    email = forms.EmailField(max_length=255, required=True)
    first_name = forms.CharField(max_length=255, required=True)
    last_name = forms.CharField(max_length=255, required=True)
    phone_number = forms.CharField(max_length=255, required=True)
    date_of_birth = forms.DateField(required=True, widget=forms.SelectDateWidget(
        years=range(1900, datetime.now().year + 1), attrs={'class': 'field'}))

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone_number', 'date_of_birth')

    def unique_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email already exists.")
        return email

    def unique_phone_number(self):
        phone = self.cleaned_data.get("phone_number")
        if User.objects.filter(phone_number=phone).exists():
            raise ValidationError("Phone number already exists.")
        return phone

class LoginForm(AuthenticationForm):
    username = forms.EmailField(label ="Email", max_length=255, required=True)
    class Meta:
        model = User
        fields = ('email',)

class CompleteProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=255, required=True)
    last_name = forms.CharField(max_length=255, required=True)
    phone_number = forms.CharField(max_length=255)
    date_of_birth = forms.DateField(required=True, widget=forms.SelectDateWidget(
        years=range(1900, datetime.now().year + 1), attrs={'class': 'field'}))
    class Meta:
        model = User
        fields = ("first_name", "last_name", "phone_number", "date_of_birth")
