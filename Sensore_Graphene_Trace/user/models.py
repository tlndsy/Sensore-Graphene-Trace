import datetime
import uuid

import Sensore_Graphene_Trace.global_constants as constants

from django.contrib.auth.models import Group
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, BaseUserManager
from django.db import models
from django_resized import ResizedImageField
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")

        email = self.normalize_email(email)

        user = self.model(
            email=email,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", "ADMIN")
        extra_fields.setdefault("date_of_birth", datetime.date.today())

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
    fist_line = models.CharField(max_length=100)
    second_line = models.CharField(max_length=100, blank=True)
    town = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.fist_line}, {self.postal_code}"

class User(AbstractBaseUser, PermissionsMixin):
    class Roles(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        CLINICIAN = "CLINICIAN", "Clinician"
        PATIENT = "PATIENT", "Patient"

    class FontSize(models.IntegerChoices):
        SMALL = constants.SMALL_FONT_SIZE, "Small"
        MEDIUM = constants.MEDIUM_FONT_SIZE, "Medium"
        LARGE = constants.LARGE_FONT_SIZE, "Large"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=255, unique=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=255)
    date_of_birth = models.DateField()

    font_size_preference = models.IntegerField(choices=FontSize.choices, default=FontSize.MEDIUM)
    address = models.ForeignKey(Address, on_delete=models.CASCADE, blank=True, null=True)
    role = models.CharField(max_length=20, choices=Roles.choices, default=Roles.PATIENT)

    def profile_picture_path(self, filename):
        return f"users/{self.id}/profile_picture/{filename}"

    profile_picture = ResizedImageField(size=[128, 128], upload_to=profile_picture_path, max_length=512, default='users/default_pfp.png', blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)

    objects = UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

class PatientClinician(models.Model):
    Patient_ID = models.ForeignKey(User, related_name='patient', on_delete=models.CASCADE)
    Clinician_ID = models.ForeignKey(User, related_name='clinician', on_delete=models.CASCADE)

    def __str__(self):
        return f"Patient: {self.Patient_ID}, Clinician: {self.Clinician_ID}"

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

    pressure_reading = models.FileField(upload_to=pressure_reading_path, max_length=512, blank=True, null=True) # change pending on needs
    metrics = models.FileField(upload_to=pressure_reading_path, max_length=512, blank=True, null=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """
        Calculations for new metrics go here, example:
        if not self.peak_pressure:
            self.peak_pressure = max(...)
        """

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Reading of: {self.reading_equipment.user}, taken at {self.timestamp}"

class Report(models.Model):
    pressure_map_reading = models.ForeignKey(PressureMapReading, on_delete=models.SET_NULL, null=True)
    content = models.TextField()

    def __str__(self):
        return f"Report belonging to {self.pressure_map_reading.reading_equipment.user}, made at {self.pressure_map_reading.timestamp}"

class Conversation(models.Model):
    subject = models.CharField(max_length=255)

    def __str__(self):
        return self.subject

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sender')
    recipient = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='recipient')
    pressure_map_reading = models.ForeignKey(PressureMapReading, on_delete=models.SET_NULL, blank=True, null=True)

    def attachment_path(self, filename):
        return f"users/{self.sender.id}/conversation_{self.conversation.id}/sent_items/{filename}"

    attachment = models.ImageField(upload_to=attachment_path, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    read_receipt = models.BooleanField(default=False)
    content = models.TextField()

    def __str__(self):
        return f"Message from {self.sender}, to {self.recipient}, made at {self.timestamp}"



