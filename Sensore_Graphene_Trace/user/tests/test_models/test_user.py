from django.test import TestCase
from django.db import IntegrityError
from user.models import User
import datetime


class UserModelAndManagerTests(TestCase):
    def setUp(self):
        self.user_data = {
            "email": "test@example.com",
            "password": "securepassword123",
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "123456789",
            "date_of_birth": "2000-01-01",
        }

    # -------------------------
    # UserManager Tests
    # -------------------------

    def test_create_user_success(self):
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.email, self.user_data["email"])
        self.assertTrue(user.check_password(self.user_data["password"]))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_active)
        self.assertEqual(user.role, User.Roles.PATIENT)
        self.assertEqual(user.font_size_preference, User.FontSize.MEDIUM)

    def test_create_user_requires_email(self):
        with self.assertRaises(ValueError) as cm:
            User.objects.create_user(
                email="",
                password="pass123",
                first_name="No",
                last_name="Email",
                phone_number="123",
                date_of_birth="2000-01-01",
            )
        self.assertIn("The Email field must be set", str(cm.exception))

    def test_create_superuser_defaults(self):
        superuser = User.objects.create_superuser(
            email="admin@test.com",
            password="adminpass",
        )
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_active)
        self.assertEqual(superuser.role, User.Roles.ADMIN)
        self.assertEqual(superuser.date_of_birth, datetime.date.today())

    def test_create_superuser_with_custom_fields(self):
        dob = datetime.date(2000, 5, 5)
        superuser = User.objects.create_superuser(
            email="admin2@test.com",
            password="adminpass",
            first_name="Admin",
            last_name="User",
            date_of_birth=dob,
        )
        self.assertEqual(superuser.first_name, "Admin")
        self.assertEqual(superuser.last_name, "User")
        self.assertEqual(superuser.date_of_birth, dob)
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)

    def test_create_superuser_must_be_staff(self):
        with self.assertRaises(ValueError) as cm:
            User.objects.create_superuser(
                email="fail@test.com",
                password="failpass",
                is_staff=False,
            )
        self.assertIn("Superuser must have is_staff=True.", str(cm.exception))

    def test_create_superuser_must_be_superuser(self):
        with self.assertRaises(ValueError) as cm:
            User.objects.create_superuser(
                email="fail2@test.com",
                password="failpass",
                is_superuser=False,
            )
        self.assertIn("Superuser must have is_superuser=True.", str(cm.exception))

    def test_email_is_normalized(self):
        user = User.objects.create_user(
            email="MiXeDCaSe@Test.COM",
            password="pass123",
            first_name="John",
            last_name="Doe",
            phone_number="123",
            date_of_birth="1990-01-01",
        )
        self.assertEqual(user.email, "MiXeDCaSe@test.com")

    # -------------------------
    # User Model Tests
    # -------------------------

    def test_email_must_be_unique(self):
        User.objects.create_user(**self.user_data)
        with self.assertRaises(IntegrityError):
            User.objects.create_user(**self.user_data)

    def test_str_method(self):
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), self.user_data["email"])

    def test_profile_picture_path(self):
        user = User.objects.create_user(**self.user_data)
        path = user.profile_picture_path("image.png")
        self.assertEqual(path, f"users/{user.id}/profile_picture/image.png")

    def test_default_profile_picture(self):
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.profile_picture.name, "users/default_pfp.png")

    def test_role_choices(self):
        user = User.objects.create_user(
            **self.user_data,
            role=User.Roles.ADMIN
        )
        self.assertEqual(user.role, User.Roles.ADMIN)

    def test_font_size_choices(self):
        user = User.objects.create_user(
            **self.user_data,
            font_size_preference=User.FontSize.LARGE
        )
        self.assertEqual(user.font_size_preference, User.FontSize.LARGE)

    def test_date_fields_auto_set(self):
        user = User.objects.create_user(**self.user_data)
        self.assertIsNotNone(user.date_joined)
        self.assertIsNotNone(user.last_login)
