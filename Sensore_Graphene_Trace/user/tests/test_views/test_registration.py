from user.models import User
from user.mixins import UserTestSetupMixin


class UserRegistrationViewTests(UserTestSetupMixin):
    def test_valid_registration(self):
        response = self.client.post(self.url, {
            "form_type": "register",
            "email": "patient@email.com",
            "phone_number": "+447911123456",
            "first_name": "John",
            "last_name": "Doe",
            "password1": "Password?123",
            "password2": "Password?123",
            "date_of_birth": "1990-01-01",
        })
        self.assertEqual(response.status_code, 302)  # Checks user has been redirected
        self.assertTrue(User.objects.filter(email="patient@email.com").exists())  # Checks user is created

    def test_invalid_email_registration(self):
        response = self.client.get(self.url, {
            "form_type": "register",
            "email": "patientemail.com",
            "phone_number": "+447911123456",
            "first_name": "John",
            "last_name": "Doe",
            "password1": "Password?123",
            "password2": "Password?123",
            "date_of_birth": "1990-01-01",
        })
        self.assertEqual(response.status_code, 200)  # Checks user hasn't been redirected
        self.assertFalse(User.objects.filter(email="patientemail.com").exists())  # Checks user isn't created

    def test_invalid_phone_number_registration(self):
        response = self.client.get(self.url, {
            "form_type": "register",
            "email": "patient@email.com",
            "phone_number": "+123456789",
            "first_name": "John",
            "last_name": "Doe",
            "password1": "Password?123",
            "password2": "Password?123",
            "date_of_birth": "1990-01-01",
        })
        self.assertEqual(response.status_code, 200)  # Checks user hasn't been redirected
        self.assertFalse(User.objects.filter(phone_number="+123456789").exists())  # Checks user isn't created

    def test_invalid_password_registration(self):
        response = self.client.get(self.url, {
            "form_type": "register",
            "email": "patient@email.com",
            "phone_number": "+447911123456",
            "first_name": "John",
            "last_name": "Doe",
            "password1": "password",
            "password2": "password",
            "date_of_birth": "1990-01-01",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(password="password").exists())

    def test_mismatched_password_registration(self):
        response = self.client.get(self.url, {
            "form_type": "register",
            "email": "patient@email.com",
            "phone_number": "+447911123456",
            "first_name": "John",
            "last_name": "Doe",
            "password1": "Password?123",
            "password2": "Password123",
            "date_of_birth": "1990-01-01",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(password="Password?123").exists())

    def test_password_too_short(self):
        response = self.client.post(self.url, {
            "form_type": "register",
            "email": "test@email.com",
            "phone_number": "+447911123456",
            "first_name": "John",
            "last_name": "Doe",
            "password1": "123",
            "password2": "123",
            "date_of_birth": "1990-01-01",
        })
        self.assertEqual(response.status_code, 200)

    def test_missing_fields_registration(self):
        data = {
            "form_type": "register",
            "email": "patient@email.com",
            "phone_number": "+447911123456",
            "first_name": "John",
            "last_name": "Doe",
            "password1": "Password?123",
            "password2": "Password?123",
            "date_of_birth": "1990-01-01",
        }
        for field in data:
            if field == "form_type":
                continue
            test_data = data.copy()
            test_data[field] = ""
            response = self.client.post(self.url, test_data)
            self.assertEqual(response.status_code, 200)
            self.assertFalse(User.objects.filter(email="patient@email.com").exists())

    def test_duplicate_email_registration(self):
        User.objects.create_user(
            email="patient@email.com",
            password="Password?123",
            first_name="John",
            last_name="Doe"
        )
        response = self.client.post(self.url, {
            "form_type": "register",
            "email": "patient@email.com",
            "phone_number": "+447911123456",
            "first_name": "Jane",
            "last_name": "Doe",
            "password1": "Password?123",
            "password2": "Password?123",
            "date_of_birth": "1990-01-01",
        })
        self.assertEqual(response.status_code, 200)

    def test_duplicate_phone_registration(self):
        User.objects.create_user(
            email="test1@email.com",
            password="Password?123",
            first_name="John",
            last_name="Doe",
            phone_number="+447911123456"
        )
        response = self.client.post(self.url, {
            "form_type": "register",
            "email": "test2@email.com",
            "phone_number": "+447911123456",
            "first_name": "Jane",
            "last_name": "Doe",
            "password1": "Password?123",
            "password2": "Password?123",
            "date_of_birth": "1990-01-01",
        })
        self.assertEqual(response.status_code, 200)

    def test_future_date_of_birth(self):
        response = self.client.post(self.url, {
            "form_type": "register",
            "email": "test@email.com",
            "phone_number": "+447911123456",
            "first_name": "John",
            "last_name": "Doe",
            "password1": "Password?123",
            "password2": "Password?123",
            "date_of_birth": "2100-01-01",
        })
        self.assertEqual(response.status_code, 200)

    def test_default_role_patient(self):
        self.client.post(self.url, {
            "form_type": "register",
            "email": "patient@email.com",
            "phone_number": "+447911123456",
            "first_name": "John",
            "last_name": "Doe",
            "password1": "Password?123",
            "password2": "Password?123",
            "date_of_birth": "1990-01-01",
        })
        user = User.objects.get(email="patient@email.com")
        self.assertEqual(user.role, User.Roles.PATIENT)
