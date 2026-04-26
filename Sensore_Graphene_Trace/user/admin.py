from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import *


# Register your models here.


# Force admin to user custom user model instead of default
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
                "profile_picture",
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
                "phone_number",
                "date_of_birth",
                "address",
                "profile_picture",
                "role",
                "is_staff",
                "is_superuser",
            ),
        }),
    )

    readonly_fields = ("last_login", "date_joined")

# Force admin to use ConversationManager
@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):

    def save_model(self, request, obj, form, change):
        if not change:
            user1, user2 = form.cleaned_data['participants']

            convo = Conversation.objects.create_conversation(
                user1=user1,
                user2=user2,
                subject=obj.subject
            )

            obj.pk = convo.pk  # bind admin object to created one
        else:
            super().save_model(request, obj, form, change)

admin.site.register(PatientClinician)
admin.site.register(Address)
admin.site.register(NotificationType)
admin.site.register(ProductInfo)
admin.site.register(ReadingEquipment)
admin.site.register(PressureMapReading)
admin.site.register(Report)
admin.site.register(Message)
admin.site.register(PasswordResetCode)
