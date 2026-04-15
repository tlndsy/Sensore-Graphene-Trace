import datetime

from django.test import TestCase, Client
from django.contrib.auth.models import Group
from django.urls import reverse

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

from unittest.mock import patch

from Sensore_Graphene_Trace import global_constants as constants
from user.models import User
from user.mixins import UserTestSetupMixin


# Create your tests here.
class UserLoginViewTests(UserTestSetupMixin):
    # Home views
    def test_home_page_loads(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "user_home.html")

    # Test Logins
    def test_valid_patient_login(self):
        self.client.login(email=self.valid_patient.email, password='Password?123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_home.html')

    def test_valid_clinician_login(self):
        self.client.login(email=self.valid_clinician.email, password='Password?123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_home.html')

    def test_valid_admin_login(self):
        self.client.login(email=self.valid_admin.email, password='Password?123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_home.html')

    def test_login_creates_session(self):
        self.client.login(email=self.valid_patient.email, password="Password?123")
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_invalid_password_login(self):
        self.client.login(email=self.valid_patient.email, password='Password?')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_home.html')

    def test_invalid_email_login(self):
        self.client.login(email="email.com", password='Password?123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_home.html')

    def test_missing_email_login(self):
        self.client.login(email="", password='Password?123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_home.html')

    def test_missing_password_login(self):
        self.client.login(email=self.valid_patient.email, password='')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_home.html')

    # Test redirects
    def test_patient_redirect(self):
        self.client.force_login(self.valid_patient)
        response = self.client.get(reverse("user:redirect_to_home"))
        self.assertRedirects(response, reverse("user:patient:home"))

    def test_clinician_redirect(self):
        self.client.force_login(self.valid_clinician)
        response = self.client.get(reverse("user:redirect_to_home"))
        self.assertRedirects(response, reverse("user:clinician:profile"))

    def test_admin_redirect(self):
        self.client.force_login(self.valid_admin)
        response = self.client.get(reverse("user:redirect_to_home"))
        self.assertRedirects(response, reverse("user:administrator:home"))

    def test_unregistered_google_login_redirect(self):
        self.client.force_login(self.unregistered_google_user)
        response = self.client.get(reverse("user:redirect_to_home"))
        self.assertRedirects(response, reverse("user:complete_profile"))

    def test_registered_google_login_redirect(self):
        self.client.force_login(self.registered_google_user)
        response = self.client.get(reverse("user:redirect_to_home"))
        self.assertRedirects(response, reverse("user:patient:home"))

    def test_unauthenticated_user_redirect(self):
        response = self.client.get(reverse("user:redirect_to_home"))
        self.assertRedirects(response, reverse("home"))

    def test_user_without_role_redirect(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("user:redirect_to_home"))
        self.assertRedirects(response, reverse("home"))
