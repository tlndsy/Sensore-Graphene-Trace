import os

from django.test import TestCase, override_settings
from django.db import IntegrityError
from django.core.files.uploadedfile import SimpleUploadedFile
from user.models import User, Address
from PIL import Image
import io
import datetime
import tempfile
import shutil


class UserModelAndManagerTests(TestCase):
    def setUp(self):
        self.user_data = {
            "email": "test@example.com",
            "password": "securepassword123",
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "123456789",
            "date_of_birth": datetime.date(2000, 5, 5),
        }

        # Temporary directory for image files
        self.temp_media_root = tempfile.mkdtemp()

    def tearDown(self):
        # Remove all files created in the temporary media root after each test
        shutil.rmtree(self.temp_media_root, ignore_errors=True)

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
                date_of_birth=datetime.date(2000, 5, 5),
            )
        self.assertIn("The Email field must be set", str(cm.exception))

    def test_create_user_requires_first_name(self):
        with self.assertRaises(ValueError) as cm:
            User.objects.create_user(
                email="test@example.com",
                password="pass123",
                first_name="",
                last_name="Doe",
                phone_number="123",
                date_of_birth=datetime.date(2000, 5, 5),
            )
        self.assertIn("Users must have a first name", str(cm.exception))

    def test_create_user_requires_last_name(self):
        with self.assertRaises(ValueError) as cm:
            User.objects.create_user(
                email="test@example.com",
                password="pass123",
                first_name="John",
                last_name="",
                phone_number="123",
                date_of_birth=datetime.date(2000, 5, 5),
            )
        self.assertIn("Users must have a last name", str(cm.exception))

    def test_create_user_requires_dob(self):
        with self.assertRaises(ValueError) as cm:
            User.objects.create_user(
                email="test@example.com",
                password="pass123",
                first_name="John",
                last_name="Doe",
                phone_number="123",
                date_of_birth=None,
            )
        self.assertIn("Users must have a date of birth", str(cm.exception))


    def test_create_user_requires_dob_in_past(self):
        with self.assertRaises(ValueError) as cm:
            User.objects.create_user(
                email="test@example.com",
                password="pass123",
                first_name="No",
                last_name="Email",
                phone_number="123",
                date_of_birth=datetime.date.today() + datetime.timedelta(days=1),
            )
        self.assertIn("Date of birth must be in the past", str(cm.exception))

    def test_create_superuser_defaults(self):
        superuser = User.objects.create_superuser(
            email="admin@test.com",
            first_name="Admin",
            last_name="Test",
            date_of_birth=datetime.date(1990, 1, 1),
            password="adminpass",
        )
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_active)
        self.assertEqual(superuser.role, User.Roles.ADMIN)
        self.assertEqual(superuser.date_of_birth, datetime.date(1990, 1, 1))

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
                first_name="Admin",
                last_name="Test",
                date_of_birth=datetime.date(2000, 5, 5),
                password="failpass",
                is_staff=False,
            )
        self.assertIn("Superuser must have is_staff=True.", str(cm.exception))

    def test_create_superuser_must_be_superuser(self):
        with self.assertRaises(ValueError) as cm:
            User.objects.create_superuser(
                email="fail2@test.com",
                first_name="Admin",
                last_name="Test",
                date_of_birth=datetime.date(2000, 5, 5),
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
            date_of_birth=datetime.date(2000, 5, 5),
        )
        self.assertEqual(user.email, "mixedcase@test.com")

    def test_user_manager_enforced(self):

        with self.assertRaises(RuntimeError) as ctx:
            user = User.objects.create(
                email="test@example.com",
                password="pass123",
                first_name="John",
                last_name="Doe",
                phone_number="123",
                date_of_birth=datetime.date(2000, 5, 5)
            )


        self.assertIn("Use User.objects.create_user()", str(ctx.exception))

    # -------------------------
    # User Model Tests
    # -------------------------

    def test_email_must_be_unique(self):
        User.objects.create_user(**self.user_data)
        with self.assertRaises(IntegrityError):
            User.objects.create_user(**self.user_data)

    def test_str_method(self):
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user),
                         f"{self.user_data["email"]} - ({self.user_data["first_name"]} {self.user_data["last_name"]})")

    def test_profile_picture_path(self):
        user = User.objects.create_user(**self.user_data)
        path = user.profile_picture_path("image.png")
        self.assertEqual(path, f"users/{user.id}/profile_picture/image.png")

    def test_default_profile_picture(self):
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.profile_picture.name, "users/default_pfp.png")

    @override_settings(MEDIA_ROOT=None)
    def test_profile_picture_is_resized(self):
        def create_test_image(size=(300, 300), color=(255, 0, 0)):
            file = io.BytesIO()
            image = Image.new("RGB", size, color)
            image.save(file, format='JPEG')
            file.seek(0)
            return file

        with override_settings(MEDIA_ROOT=self.temp_media_root):
            image_file = create_test_image()

            uploaded_file = SimpleUploadedFile(
                name='test.jpg',
                content=image_file.read(),
                content_type='image/jpeg'
            )

            user = User.objects.create_user(
                **self.user_data,
                profile_picture=uploaded_file
            )

            user.refresh_from_db()
            image = Image.open(user.profile_picture)

            self.assertEqual(image.size, (128, 128))

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
        self.assertEqual(user.date_joined.date(), datetime.date.today())

    def test_address_field_null_on_delete(self):

        address = Address.objects.create(
            first_line="123 Test St",
            second_line="Testford",
            town="Test Town",
            postal_code="PE01 1AA"
        )
        user = User.objects.create_user(**self.user_data, address=address)

        self.assertEqual(user.address, address)

        address.delete()
        user.refresh_from_db()

        self.assertIsNone(user.address)


