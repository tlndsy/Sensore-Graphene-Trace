from django import forms
from user import models
from user.models import ProductInfo, ReadingEquipment, User


class RegisterDevice(forms.ModelForm):
    product_info = forms.ModelChoiceField(
        queryset=ProductInfo.objects.all(),
        empty_label="Select a product",
        widget=forms.Select(attrs={"class": "form-control"})
    )

    class Meta:
        model = ReadingEquipment
        fields = ["product_info", "serial_number", "custom_name"]
        widgets = {
            "serial_number": forms.TextInput(attrs={"class": "form-control"}),
            "custom_name": forms.TextInput(attrs={"class": "form-control"}),
        }