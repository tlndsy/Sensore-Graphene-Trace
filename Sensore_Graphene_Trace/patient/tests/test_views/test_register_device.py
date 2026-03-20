from datetime import datetime
import uuid

from django.test import TestCase, Client
from django.contrib.auth.models import Group
from django.urls import reverse

from unittest.mock import patch

from Sensore_Graphene_Trace import global_constants as constants
from user.models import User, ProductInfo, ReadingEquipment



# Create your tests here.
class PatientViewDevicesViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse("user:patient:registerDevice")

        self.patient_group = Group.objects.create(name=constants.PATIENT)
        self.clinician_group = Group.objects.create(name=constants.CLINICIAN)
        self.admin_group = Group.objects.create(name=constants.ADMIN)

        self.user = User.objects.create_user(
            email="user@test.com", password="pass", date_of_birth=datetime.now()
        )
        self.user.groups.clear()

        self.patient_user = User.objects.create_user(
            email="patient_user@test.com", password="pass", date_of_birth=datetime.now(), role=constants.PATIENT
        )

        self.alt_patient_user = User.objects.create_user(
            email="alt_patient_user@test.com", password="pass", date_of_birth=datetime.now(), role=constants.PATIENT
        )

        self.clinician_user = User.objects.create_user(
            email="clinician_user@test.com", password="pass", date_of_birth=datetime.now(), role=constants.CLINICIAN
        )

        self.multi_group_user = User.objects.create_user(
            email="multi_group_user@test.com", password="pass", date_of_birth=datetime.now()
        )
        self.multi_group_user.groups.add(self.patient_group, self.clinician_group)

        self.admin_user = User.objects.create_user(
            email="admin_user@test.com", password="pass", date_of_birth=datetime.now(), role=constants.ADMIN
        )

        self.superuser = User.objects.create_superuser(
            email="superuser@test.com", password="pass", date_of_birth=datetime.now()
        )

        self.product_info_test = ProductInfo.objects.create(
            model="Test Device Model",
            manufacturer="Test Manufacturer",
            resolution_width=32,
            resolution_height=32,
            refresh_rate=15
        )

        ReadingEquipment.objects.all().delete()

    def test_requires_login(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("user:home"), response.url)

    def test_allows_patient_user(self):
        self.client.login(email="patient_user@test.com", password="pass")

        with patch("user.utils.notifications.get_notification_count", return_value=5):
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "patient/patient_register_device.html")
        self.assertEqual(response.context["num_notifications"], 5)

    def test_allows_admin_user(self):
        self.client.login(email="admin_user@test.com", password="pass")

        with patch("user.utils.notifications.get_notification_count", return_value=3):
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["num_notifications"], 3)

    def test_allows_superuser(self):
        self.client.login(email="superuser@test.com", password="pass")

        with patch("user.utils.notifications.get_notification_count", return_value=7):
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["num_notifications"], 7)

    def test_allow_valid_user_in_multiple_groups(self):
        self.client.login(email="multi_group_user@test.com", password="pass")

        with patch("user.utils.notifications.get_notification_count", return_value=9):
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["num_notifications"], 9)

    def test_forbidden_for_user_without_group(self):
        self.client.login(email="clinician_user@test.com", password="pass")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_forbidden_for_anonymous_user(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("user:home"), response.url)

    def test_notification_count_in_context(self):
        self.client.login(email="patient_user@test.com", password="pass")

        with patch("user.utils.notifications.get_notification_count", return_value=5):
            response = self.client.get(self.url)

        self.assertIn("num_notifications", response.context)
        self.assertEqual(response.context["num_notifications"], 5)

    def test_notification_count_called_with_correct_user(self):
        self.client.login(email="patient_user@test.com", password="pass")

        with patch("user.utils.notifications.get_notification_count") as mock_func:
            mock_func.return_value = 10

            response = self.client.get(self.url)

        mock_func.assert_called_once_with(self.patient_user)
        self.assertEqual(response.context["num_notifications"], 10)

    def test_notification_count_zero(self):
        self.client.login(email="patient_user@test.com", password="pass")

        with patch("user.utils.notifications.get_notification_count", return_value=0):
            response = self.client.get(self.url)

        self.assertEqual(response.context["num_notifications"], 0)

    def test_get_renders_form(self):
        self.client.login(email="patient_user@test.com", password="pass")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "patient/patient_register_device.html")
        self.assertIn("form", response.context)

    def test_post_creates_device_and_assigns_user(self):
        self.client.login(email="patient_user@test.com", password="pass")

        data = {
            "product_info": self.product_info_test.id,
            "serial_number": "12345",
            "custom_name": "test device",
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("user:patient:viewDevices"))

        device = ReadingEquipment.objects.filter(user=self.patient_user).first()
        self.assertIsNotNone(device)
        self.assertEqual(device.user, self.patient_user)

    def test_post_invalid_data(self):
        self.client.login(email="patient_user@test.com", password="pass")

        data = {
            "product_info": self.product_info_test.id,
            "serial_number": "",  # missing required field
            "custom_name": "test device",
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)

        form = response.context["form"]

        self.assertFalse(form.is_valid())
        self.assertIn("serial_number", form.errors)
        self.assertEqual(form.errors["serial_number"], ["This field is required."])

    def test_user_field_cannot_be_spoofed(self):
        self.client.login(email="patient_user@test.com", password="pass")

        data = {
            "product_info": self.product_info_test.id,
            "serial_number": "12345",
            "user": self.alt_patient_user,  # malicious attempt
            "custom_name": "test device",
        }

        self.client.post(self.url, data)

        device = ReadingEquipment.objects.first()
        self.assertEqual(device.user, self.patient_user)
        self.assertEqual(ReadingEquipment.objects.filter(user=self.alt_patient_user).count(), 0)