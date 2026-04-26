import datetime

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, Client
from django.contrib.auth.models import Group, Permission
from django.urls import reverse

from unittest.mock import patch

from Sensore_Graphene_Trace import global_constants as constants
from user.models import User, ProductInfo, ReadingEquipment


# Create your tests here.
class AdminGenericListViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse("user:administrator:generic_list", args=["user", "readingequipment"])



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
        content_type = ContentType.objects.get_for_model(ReadingEquipment)
        permission = Permission.objects.get(
            codename="view_readingequipment",
            content_type=content_type,
        )
        self.admin_group.permissions.add(permission)
        self.admin_group.permissions.add(Permission.objects.get(
            codename="view_productinfo",
            content_type=ContentType.objects.get_for_model(ProductInfo),
        ))

        self.superuser = User.objects.create_superuser(
            email="superuser@test.com",
            first_name="Test",
            last_name="Superuser",
            password="pass",
            date_of_birth=datetime.date(2000, 5, 5)
        )

        ReadingEquipment.objects.all().delete()

        self.product_info1 = ProductInfo.objects.create(
            model="TestModel1",
            manufacturer="TestManufacturer",
            resolution_width=32,
            resolution_height=32,
            refresh_rate=15,
        )
        self.product_info2 = ProductInfo.objects.create(
            model="TestModel2",
            manufacturer="TestManufacturer",
            resolution_width=32,
            resolution_height=32,
            refresh_rate=15,
        )
        self.readingEquipment1 = ReadingEquipment.objects.create(
            product_info=self.product_info1,
            serial_number="TestEquipment1",
            user=self.patient_user,
        )
        self.readingEquipment2 = ReadingEquipment.objects.create(
            product_info=self.product_info2,
            serial_number="TestEquipment2",
            user=self.patient_user,
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
        self.assertTemplateUsed(response, "administrator/generic_list.html")
        self.assertTemplateUsed(response, "user_layout.html")
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

    def test_all_objects_in_context(self):
        self.client.login(email="superuser@test.com", password="pass")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        for obj in response.context["objects"]:
            self.assertIn(obj, [self.readingEquipment1, self.readingEquipment2])

    def test_object_ordering(self):
        self.client.login(email="superuser@test.com", password="pass")

        url = f"{self.url}?sort=serial_number"

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["objects"][0], self.readingEquipment1)
        self.assertEqual(response.context["objects"][1], self.readingEquipment2)

        # test reverse
        url = f"{self.url}?sort=-serial_number"

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["objects"][0], self.readingEquipment2)
        self.assertEqual(response.context["objects"][1], self.readingEquipment1)

    def test_object_filtering(self):
        self.client.login(email="superuser@test.com", password="pass")

        url = f"{self.url}?q=&id=&product_info=&serial_number=TestEquipment1&user=&custom_name="

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.readingEquipment1, response.context["objects"])
        self.assertNotIn(self.readingEquipment2, response.context["objects"])



