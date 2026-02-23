# forms.py
from django import forms
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from user.models import User


class AdminUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "date_of_birth",
            "address",
            "role",
            "font_size_preference",
            "profile_picture",
            "is_active",
            "is_staff",
        ]

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords do not match")

        validate_password(password2)
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)

        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()

            # Automatically assign Django Group
            group_name = user.role
            group, created = Group.objects.get_or_create(name=group_name)
            user.groups.set([group])

        return user

class AdminUserFilterForm(forms.Form):
    email = forms.CharField(required=False)
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)

    role = forms.ChoiceField(
        required=False,
        choices=[('', 'All')] + list(User.Roles.choices)
    )

    is_active = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All'),
            ('true', 'Active'),
            ('false', 'Inactive'),
        ]
    )

    joined_after = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    joined_before = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    ordering = forms.ChoiceField(
        required=False,
        choices=[
            ('newest', 'Newest Accounts'),
            ('oldest', 'Oldest Accounts'),
        ]
    )
class AdminUserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "date_of_birth",
            "role",
            "is_active",
            "is_staff",
            "font_size_preference",
            "address",
        ]