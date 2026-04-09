import datetime

from django.test import TestCase, Client
from django.contrib.auth.models import Group
from django.urls import reverse

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

from unittest.mock import patch

from Sensore_Graphene_Trace import global_constants as constants
from user.models import User, PasswordResetCode
from user.mixins import UserTestSetupMixin


class UserConfirmPasswordResetView(UserTestSetupMixin):
    def test_confirm_password_reset_valid(self):
        PasswordResetCode.objects.create(user=self.valid_patient, code="123456")
        response = self.client.post(self.url, {
            "form_type": "confirm_reset",
            "email": self.valid_patient.email,
            "code": "123456",
            "password": "Newpassword?123"
        })
        self.assertRedirects(response, reverse("home"))
        self.valid_patient.refresh_from_db()
        self.assertTrue(self.valid_patient.check_password("NewPassword?123"))
        self.assertFalse(self.valid_patient.check_password("Password?123"))

    def test_confirm_password_reset_invalid_code(self):
        PasswordResetCode.objects.create(user=self.valid_patient, code="123456")
        response = self.client.post(self.url, {
            "form_type": "confirm_reset",
            "email": self.valid_patient.email,
            "code": "999999",
            "password": "Newpassword?123"
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid or expired code.")

    @patch("user.models.PasswordResetCode.is_valid", return_value=False)
    def test_confirm_password_reset_expired_code(self, mock_valid):
        PasswordResetCode.objects.create(user=self.valid_patient, code="123456")
        response = self.client.post(self.url, {
            "form_type": "confirm_reset",
            "email": self.valid_patient.email,
            "code": "123456",
            "password": "Newpassword?123"
        })
        self.assertContains(response, "Invalid or expired code.")

    def test_confirm_password_reset_user_not_found(self):
        response = self.client.post(self.url, {
            "form_type": "confirm_reset",
            "email": "fake@email.com",
            "code": "123456",
            "password": "NewPassword?123"
        })
        self.assertContains(response, "Invalid or expired code.")
