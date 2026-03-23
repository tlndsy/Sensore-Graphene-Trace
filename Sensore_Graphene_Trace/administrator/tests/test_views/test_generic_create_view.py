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


    def test_get_form_class_uses_modelform_factory(self):
        self.client.login(email="admin_user@test.com", password="pass")

        # Ensure the home view still works for admin_user
        with patch("user.utils.notifications.get_notification_count", return_value=1):
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        # Now exercise the GenericCreateView for a model in the `user` app.
        create_url = reverse("user:administrator:generic_create", args=["user", "productinfo"])

        # Patch the modelform_factory imported in the administrator.views module to assert it's used
        with patch("administrator.views.modelform_factory") as mock_mff:
            # Return a simple form class so the view can render
            class DummyForm:
                pass

            mock_mff.return_value = DummyForm

            # Login as superuser (has all permissions) and GET the create page
            self.client.login(email="superuser@test.com", password="pass")
            response = self.client.get(create_url)

        mock_mff.assert_called_once()
        # The first argument should be the ProductInfo model class
        called_model = mock_mff.call_args[0][0]
        self.assertEqual(called_model._meta.model_name, "productinfo")
        # ensure view rendered the create template
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "administrator/generic_create.html")

    def test_post_creates_productinfo_and_redirects(self):
        # Login as superuser to bypass permission requirements
        self.client.login(email="superuser@test.com", password="pass")

        create_url = reverse("user:administrator:generic_create", args=["user", "productinfo"])

        post_data = {
            "model": "TestModel",
            "manufacturer": "TestManufacturer",
            "resolution_width": 32,
            "resolution_height": 32,
            "refresh_rate": 15,
        }

        response = self.client.post(create_url, data=post_data)

        # Should redirect to the generic list for productinfo
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("user:administrator:generic_list", args=["user", "productinfo"]), response.url)

        # Confirm the object was created
        from user.models import ProductInfo

        self.assertTrue(ProductInfo.objects.filter(model="TestModel", manufacturer="TestManufacturer").exists())

    def test_permission_denied_for_non_admin_on_generic_create(self):
        # Login as a patient user, should be denied access to generic_create
        self.client.login(email="patient_user@test.com", password="pass")

        create_url = reverse("user:administrator:generic_create", args=["user", "productinfo"])
        response = self.client.get(create_url)

        self.assertEqual(response.status_code, 403)
