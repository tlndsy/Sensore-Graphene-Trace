import uuid

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, BaseUserManager
from django.db import models


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

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=255, unique=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=255)
    date_of_birth = models.DateField()

    address = models.ForeignKey(Address, on_delete=models.CASCADE, blank=True, null=True)
    role = models.CharField(max_length=20, choices=Roles.choices, default=Roles.PATIENT)

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

class NotificationType(models.Model):
    type = models.CharField(max_length=25)
    users = models.ManyToManyField(User)

    def __str__(self):
        return f"{self.type}"

class DeviceInfo(models.Model):
    model = models.CharField(max_length=255)
    manufacturer = models.CharField(max_length=255)
    resolution_width = models.PositiveIntegerField(default=0)
    resolution_height = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.model

class ReadingEquipment(models.Model):
    product = models.ForeignKey(DeviceInfo, on_delete=models.SET_NULL, null=True)
    serial_number = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.product.model}, Serial Number: {self.serial_number}, Belonging To: {self.user}"

class PressureMapReading(models.Model):
    reading_equipment = models.ForeignKey(ReadingEquipment, on_delete=models.SET_NULL, null=True)
    reading = models.FileField(upload_to=f'pressure_maps/{reading_equipment.user.id}', blank=True, null=True) # change pending on needs
    timestamp = models.DateTimeField(auto_now_add=True)
    peak_pressure = models.PositiveSmallIntegerField()
    contact_area = models.PositiveSmallIntegerField()
    # New metrics go here

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
    attachment = models.ImageField(upload_to=f'conversations/{sender.id}', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    read_receipt = models.BooleanField(default=False)
    content = models.TextField()

    def __str__(self):
        return f"Message from {self.sender}, to {self.recipient}, made at {self.timestamp}"



