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
        self.url = reverse("user:patient:viewDevices")

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

    def test_requires_login(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("user:home"), response.url)

    def test_allows_patient_user(self):
        self.client.login(email="patient_user@test.com", password="pass")

        with patch("user.utils.notifications.get_notification_count", return_value=5):
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "patient/patient_view_devices.html")
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

    def test_devices_in_context(self):
        self.client.login(email="patient_user@test.com", password="pass")

        with patch("user.utils.notifications.get_notification_count", return_value=0):
            response = self.client.get(self.url)

        self.assertIn("devices", response.context)

    def test_devices_in_context_correct_user(self):
        ReadingEquipment.objects.filter(user=self.patient_user).delete()
        # Create multiple devices two patients to ensure only the correct user's devices are returned
        for i in range(5):
            ReadingEquipment.objects.create(
                product_info=self.product_info_test,
                serial_number=str(uuid.uuid4()),
                user=self.patient_user,
            )
            ReadingEquipment.objects.create(
                product_info=self.product_info_test,
                serial_number=str(uuid.uuid4()),
                user=self.alt_patient_user,
            )

        self.client.login(email="patient_user@test.com", password="pass")

        with patch("user.utils.notifications.get_notification_count", return_value=0):
            response = self.client.get(self.url)

        devices = response.context["devices"]
        for device in devices:
            self.assertEqual(device.user, self.patient_user)

    def test_devices_in_context_no_devices(self):
        ReadingEquipment.objects.filter(user=self.patient_user).delete()

        self.client.login(email="patient_user@test.com", password="pass")

        with patch("user.utils.notifications.get_notification_count", return_value=0):
            response = self.client.get(self.url)

        devices = response.context["devices"]

        self.assertEqual(len(devices), 0)

    def test_devices_in_context_multiple_devices(self):
        ReadingEquipment.objects.filter(user=self.patient_user).delete()
        # Create multiple devices for the user
        for i in range(5):
            ReadingEquipment.objects.create(
                product_info=self.product_info_test,
                serial_number=str(uuid.uuid4()),
                user=self.patient_user,
            )

        self.client.login(email="patient_user@test.com", password="pass")

        with patch("user.utils.notifications.get_notification_count", return_value=0):
            response = self.client.get(self.url)

        devices = response.context["devices"]

        self.assertEqual(len(devices), 5)
