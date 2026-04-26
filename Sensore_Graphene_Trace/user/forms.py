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

    # Checks that the user's email is unique
    def unique_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email already exists.")
        return email

    # Checks that the user's phone number is unique
    def unique_phone_number(self):
        phone = self.cleaned_data.get("phone_number")
        if User.objects.filter(phone_number=phone).exists():
            raise ValidationError("Phone number already exists.")
        return phone


# Login form
class LoginForm(AuthenticationForm):
    username = forms.EmailField(label="Email", max_length=255, required=True) # Sets user name to email for DB requirements

    class Meta:
        model = User
        fields = ('email',)


# Form for the user to complete their profile (e.g., unregistered google user)
class CompleteProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=255, required=True)
    last_name = forms.CharField(max_length=255, required=True)
    phone_number = forms.CharField(max_length=255)
    date_of_birth = forms.DateField(required=True, widget=forms.SelectDateWidget(
        years=range(1900, datetime.now().year + 1), attrs={'class': 'field'}))  # Restricts dob to current day and 1900

    class Meta:
        model = User
        fields = ("first_name", "last_name", "phone_number", "date_of_birth")
