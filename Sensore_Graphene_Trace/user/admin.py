from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import *


# Register your models here.



@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("email",)
    list_display = (
        "email",
        "first_name",
        "last_name",
        "role",
        "is_staff",
        "is_active",
    )
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("email", "first_name", "last_name")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {
            "fields": (
                "first_name",
                "last_name",
                "phone_number",
                "address",
                "date_of_birth",
            )
        }),
        (_("Permissions"), {
            "fields": (
                "role",
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email",
                "password1",
                "password2",
                "first_name",
                "last_name",
                "role",
                "is_staff",
                "is_superuser",
            ),
        }),
    )

    readonly_fields = ("last_login", "date_joined")


admin.site.register(Address)
admin.site.register(NotificationType)
admin.site.register(DeviceInfo)
admin.site.register(ReadingEquipment)
admin.site.register(PressureMapReading)
admin.site.register(Report)
admin.site.register(Conversation)
admin.site.register(Message)
