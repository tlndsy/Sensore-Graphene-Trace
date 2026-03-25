import datetime
import uuid

from django.core.exceptions import ValidationError
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth.models import Group, PermissionsMixin, BaseUserManager
from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models, transaction
from django_resized import ResizedImageField

import Sensore_Graphene_Trace.global_constants as constants


class UserManager(BaseUserManager):
    @transaction.atomic
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        if not extra_fields.get("first_name"):
            raise ValueError("Users must have a first name")
        if not extra_fields.get("last_name"):
            raise ValueError("Users must have a last name")
        if not extra_fields.get("date_of_birth"):
            raise ValueError("Users must have a date of birth")
        if extra_fields.get("date_of_birth") >= datetime.date.today():
            raise ValueError("Date of birth must be in the past")

        email = self.normalize_email(email).lower()

        user = self.model(
            email=email,
            **extra_fields,
        )
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    @transaction.atomic
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields["is_active"] = True
        extra_fields["role"] = self.model.Roles.ADMIN

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(
            email=email,
            password=password,
            **extra_fields,
        )


# Create your models here.
class Address(models.Model):
    first_line = models.CharField(max_length=100)
    second_line = models.CharField(max_length=100, blank=True)
    town = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.first_line}, {self.postal_code}"


class User(AbstractBaseUser, PermissionsMixin):
    class Roles(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        CLINICIAN = "CLINICIAN", "Clinician"
        PATIENT = "PATIENT", "Patient"

    class FontSize(models.IntegerChoices):
        SMALL = constants.SMALL_FONT_SIZE, "Small"
        MEDIUM = constants.MEDIUM_FONT_SIZE, "Medium"
        LARGE = constants.LARGE_FONT_SIZE, "Large"

    class Meta:
        ordering = ["-date_joined"]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=255, unique=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    phone_number = PhoneNumberField(blank=True, null=True, unique=True)
    date_of_birth = models.DateField()

    font_size_preference = models.IntegerField(choices=FontSize.choices, default=FontSize.MEDIUM)
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, blank=True, null=True, related_name="users")
    role = models.CharField(max_length=20, choices=Roles.choices, default=Roles.PATIENT, db_index=True)

    def profile_picture_path(self, filename):
        return f"users/{self.pk}/profile_picture/{filename}"

    profile_picture = ResizedImageField(size=[128, 128], upload_to=profile_picture_path, max_length=512,
                                        default='users/default_pfp.png', blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False, db_index=True)
    is_superuser = models.BooleanField(default=False, db_index=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ["first_name", "last_name", "date_of_birth"]

    def __str__(self):
        return f"{self.email} - ({self.get_full_name()})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name


class PatientClinician(models.Model):
    patient = models.ForeignKey(User, related_name='patient_relationships', on_delete=models.CASCADE)
    clinician = models.ForeignKey(User, related_name='clinician_relationships', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['patient', 'clinician'], name='unique_patient_clinician')
        ]

    def clean(self):
        if not self.patient.groups.filter(name=User.Roles.PATIENT).exists():
            raise ValidationError("Selected patient is not a valid patient.")
        if not self.clinician.groups.filter(name=User.Roles.PATIENT).exists():
            raise ValidationError("Selected clinician is not a valid clinician.")

    def __str__(self):
        return f"Patient: {self.patient}, Clinician: {self.clinician}"

    def save(self, *args, **kwargs):
        self.full_clean()  # Ensure validation is performed before saving
        super().save(*args, **kwargs)


class NotificationType(models.Model):
    type = models.CharField(max_length=25)
    users = models.ManyToManyField(User)

    def __str__(self):
        return f"{self.type}"


class ProductInfo(models.Model):
    model = models.CharField(max_length=100)
    manufacturer = models.CharField(max_length=255)
    resolution_width = models.PositiveIntegerField(default=0)
    resolution_height = models.PositiveIntegerField(default=0)
    refresh_rate = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.model


class ReadingEquipment(models.Model):
    product_info = models.ForeignKey(ProductInfo, on_delete=models.SET_NULL, null=True)
    serial_number = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    custom_name = models.CharField(max_length=255, blank=True)

    def get_default_device_name(self):
        return f"{self.product_info.model} - {self.serial_number}"

    class Meta:
        ordering = ["-user__date_joined"]

    def save(self, *args, **kwargs):
        if not self.custom_name:
            self.custom_name = self.get_default_device_name()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product_info.model}, Serial Number: {self.serial_number}, Belonging To: {self.user}"


class PressureMapReading(models.Model):
    reading_equipment = models.ForeignKey(ReadingEquipment, on_delete=models.SET_NULL, null=True)

    # Remove colons to create valid filepath
    def pressure_reading_path(self, filename):
        timestamp = self.timestamp or timezone.now()
        safe_timestamp = timestamp.strftime("%Y%m%d_%H%M%S")
        return f"users/{self.reading_equipment.user.id}/pressure_maps/{safe_timestamp}/{filename}"

    pressure_reading = models.FileField(upload_to=pressure_reading_path, max_length=512, blank=True,
                                        null=True)  # change pending on needs
    metrics = models.FileField(upload_to=pressure_reading_path, max_length=512, blank=True, null=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"Reading of: {self.reading_equipment.user}, taken at {self.timestamp}"


class Report(models.Model):
    pressure_map_reading = models.ForeignKey(PressureMapReading, on_delete=models.SET_NULL, null=True)
    content = models.TextField()

    class Meta:
        ordering = ["-pressure_map_reading__timestamp"]

    def __str__(self):
        return f"Report belonging to {self.pressure_map_reading.reading_equipment.user}, made at {self.pressure_map_reading.timestamp}"


class Conversation(models.Model):
    subject = models.CharField(max_length=255)
    participants = models.ManyToManyField(User, related_name='conversations')
    last_message = models.ForeignKey('Message', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def clean(self):
        if self.pk:
            participants = list(self.participants.all())

            if len(participants) != 2:
                raise ValidationError("Conversation must have exactly 2 participants.")

            user1, user2 = participants

            # Check PatientClinician relationship exists or user is messaging an admin
            valid = PatientClinician.objects.filter(
                patient=user1, clinician=user2
            ).exists() or PatientClinician.objects.filter(
                patient=user2, clinician=user1
            ).exists() or user1.groups.filter(
                name__in=constants.ADMIN
            ).exists() or user2.groups.filter(
                name__in=constants.ADMIN
            ).exists()

            if not valid:
                raise ValidationError("Participants must have a valid patient-clinician relationship.")

    def __str__(self):
        return self.subject or f"Conversation {self.id}"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='received_messages')
    pressure_map_reading = models.ForeignKey(PressureMapReading, on_delete=models.SET_NULL, blank=True, null=True)

    def attachment_path(self, filename):
        sender_id = self.sender.id if self.sender else "unknown"
        conversation_id = self.conversation.id if self.conversation else "unknown"
        return f"users/{sender_id}/conversation_{conversation_id}/sent_items/{filename}"

    attachment = models.ImageField(upload_to=attachment_path, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    read_receipt = models.BooleanField(default=False)
    content = models.TextField(blank=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["conversation", "-timestamp"]),
        ]

    def save(self, *args, **kwargs):
        self.full_clean()

        super().save(*args, **kwargs)

        # Update conversation last_message + timestamp
        self.conversation.last_message = self
        self.conversation.save(update_fields=['last_message', 'updated_at'])

    def clean(self):
        if not self.conversation:
            return

        participants = self.conversation.participants.all()

        # Sender must be in conversation
        if self.sender not in participants:
            raise ValidationError("Sender is not part of this conversation.")

        # Recipient must be in conversation
        if self.recipient not in participants:
            raise ValidationError("Recipient is not part of this conversation.")

        # Sender and recipient must be different
        if self.sender == self.recipient:
            raise ValidationError("Sender and recipient cannot be the same.")

    def __str__(self):
        return f"Message from {self.sender}, to {self.recipient}, made at {self.timestamp}"
