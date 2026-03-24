import datetime

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, Client
from django.contrib.auth.models import Group, Permission
from django.urls import reverse

from unittest.mock import patch

from Sensore_Graphene_Trace import global_constants as constants
from user.models import User, ProductInfo


# Create your tests here.
class AdminGenericDeleteViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        # default to the administrator home (tests below also exercise the generic create view directly)
        self.url = reverse("user:administrator:generic_create", args=["user", "productinfo"])

        self.post_data = {
            "model": "TestModel",
            "manufacturer": "TestManufacturer",
            "resolution_width": 32,
            "resolution_height": 32,
            "refresh_rate": 15,
        }

        self.patient_group, _ = Group.objects.get_or_create(name=constants.PATIENT)
        self.clinician_group, _ = Group.objects.get_or_create(name=constants.CLINICIAN)
        self.admin_group, _ = Group.objects.get_or_create(name=constants.ADMIN)

        self.user = User.objects.create_user(
            email="user@test.com",
            first_name="Test",
            last_name="User",
            password="pass",
            date_of_birth=datetime.date(2000, 5, 5)
        )
        self.user.groups.clear()

        self.patient_user = User.objects.create_user(
            email="patient_user@test.com",
            first_name="Test",
            last_name="Patient",
            password="pass",
            date_of_birth=datetime.date(2000, 5, 5),
            role=constants.PATIENT
        )

        self.clinician_user = User.objects.create_user(
            email="clinician_user@test.com",
            first_name="Test",
            last_name="Clinician",
            password="pass",
            date_of_birth=datetime.date(2000, 5, 5),
            role=constants.CLINICIAN
        )

        self.invalid_multi_group_user = User.objects.create_user(
            email="invalid_multi_group_user@test.com",
            first_name="Invalid",
            last_name="Multi",
            password="pass",
            date_of_birth=datetime.date(2000, 5, 5)
        )
        self.invalid_multi_group_user.groups.add(self.patient_group)
        self.invalid_multi_group_user.groups.add(self.clinician_group)

        self.valid_multi_group_user = User.objects.create_user(
            email="valid_multi_group_user@test.com",
            first_name="Valid",
            last_name="Multi",
            password="pass",
            date_of_birth=datetime.date(2000, 5, 5)
        )
        self.valid_multi_group_user.groups.add(self.admin_group)
        self.valid_multi_group_user.groups.add(self.clinician_group)

        self.admin_user = User.objects.create_user(
            email="admin_user@test.com",
            first_name="Test",
            last_name="Admin",
            password="pass",
            date_of_birth=datetime.date(2000, 5, 5),
            role=constants.ADMIN
        )
        content_type = ContentType.objects.get_for_model(ProductInfo)
        permission = Permission.objects.get(
            codename="add_productinfo",
            content_type=content_type,
        )
        self.admin_group.permissions.add(permission)

        self.superuser = User.objects.create_superuser(
            email="superuser@test.com",
            first_name="Test",
            last_name="Superuser",
            password="pass",
            date_of_birth=datetime.date(2000, 5, 5)
        )

    def test_requires_login(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("user:home"), response.url)

    def test_deny_patient_user(self):
        self.client.login(email="patient_user@test.com", password="pass")
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_allows_admin_user(self):
        self.client.login(email="admin_user@test.com", password="pass")

        with patch("user.utils.notifications.get_notification_count", return_value=3):
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "administrator/generic_create.html")
        self.assertTemplateUsed(response, "administrator_layout.html")
        self.assertEqual(response.context["num_notifications"], 3)

    def test_allows_superuser(self):
        self.client.login(email="superuser@test.com", password="pass")

        with patch("user.utils.notifications.get_notification_count", return_value=7):
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["num_notifications"], 7)

    def test_allow_valid_user_in_multiple_groups(self):
        self.client.login(email="valid_multi_group_user@test.com", password="pass")

        with patch("user.utils.notifications.get_notification_count", return_value=9):
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["num_notifications"], 9)

    def test_deny_invalid_user_in_multiple_groups(self):
        self.client.login(email="invalid_multi_group_user@test.com", password="pass")
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_forbidden_for_user_without_group(self):
        self.client.login(email="user@test.com", password="pass")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_forbidden_for_anonymous_user(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("user:home"), response.url)

    def test_notification_count_in_context(self):
        self.client.login(email="admin_user@test.com", password="pass")

        with patch("user.utils.notifications.get_notification_count", return_value=5):
            response = self.client.get(self.url)

        self.assertIn("num_notifications", response.context)
        self.assertEqual(response.context["num_notifications"], 5)

    def test_notification_count_called_with_correct_user(self):
        self.client.login(email="admin_user@test.com", password="pass")

        with patch("user.utils.notifications.get_notification_count") as mock_func:
            mock_func.return_value = 10

            response = self.client.get(self.url)

        mock_func.assert_called_once_with(self.admin_user)
        self.assertEqual(response.context["num_notifications"], 10)

    def test_notification_count_zero(self):
        self.client.login(email="admin_user@test.com", password="pass")

        with patch("user.utils.notifications.get_notification_count", return_value=0):
            response = self.client.get(self.url)

        self.assertEqual(response.context["num_notifications"], 0)

    def test_post_creates_productinfo_and_redirects(self):
        # Login as superuser to bypass permission requirements
        self.client.login(email="superuser@test.com", password="pass")

        create_url = reverse("user:administrator:generic_create", args=["user", "productinfo"])


        response = self.client.post(create_url, data=self.post_data)

        # Should redirect to the generic list for productinfo
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("user:administrator:generic_list", args=["user", "productinfo"]), response.url)

        # Confirm the object was created
        self.assertTrue(ProductInfo.objects.filter(model="TestModel", manufacturer="TestManufacturer").exists())

    def test_post_forbidden_for_patient_user(self):
        self.client.login(email="patient_user@test.com", password="pass")

        response = self.client.post(self.url, data=self.post_data)

        self.assertEqual(response.status_code, 403)
        self.assertFalse(ProductInfo.objects.filter(model="TestModel", manufacturer="TestManufacturer").exists())

    def test_post_allows_admin_user(self):
        self.client.login(email="admin_user@test.com", password="pass")

        response = self.client.post(self.url, data=self.post_data)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(ProductInfo.objects.filter(model="TestModel", manufacturer="TestManufacturer").exists())

    def test_post_allows_superuser(self):
        self.client.login(email="superuser@test.com", password="pass")

        response = self.client.post(self.url, data=self.post_data)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(ProductInfo.objects.filter(model="TestModel", manufacturer="TestManufacturer").exists())

    def test_post_allow_valid_user_in_multiple_groups(self):
        self.client.login(email="valid_multi_group_user@test.com", password="pass")

        response = self.client.post(self.url, data=self.post_data)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(ProductInfo.objects.filter(model="TestModel", manufacturer="TestManufacturer").exists())

    def test_post_deny_invalid_user_in_multiple_groups(self):
        self.client.login(email="invalid_multi_group_user@test.com", password="pass")
        response = self.client.post(self.url, data=self.post_data)

        self.assertEqual(response.status_code, 403)
        self.assertFalse(ProductInfo.objects.filter(model="TestModel", manufacturer="TestManufacturer").exists())

    def test_post_forbidden_for_user_without_group(self):
        self.client.login(email="user@test.com", password="pass")

        response = self.client.post(self.url, data=self.post_data)

        self.assertEqual(response.status_code, 403)
        self.assertFalse(ProductInfo.objects.filter(model="TestModel", manufacturer="TestManufacturer").exists())