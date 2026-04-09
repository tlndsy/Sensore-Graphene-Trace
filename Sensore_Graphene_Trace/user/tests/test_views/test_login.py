import datetime

from django.test import TestCase, Client
from django.contrib.auth.models import Group
from django.urls import reverse

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

from unittest.mock import patch

from Sensore_Graphene_Trace import global_constants as constants
from user.models import User

# Create your tests here.
class UserLoginViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('user:home')

        site = Site.objects.get_current()
        social_app = SocialApp.objects.create(
            provider='google',
            name='Google',
            client_id='test-client-id',
            secret='test-secret'
        )
        social_app.sites.add(site)

        self.patient_group, _ = Group.objects.get_or_create(name=constants.PATIENT)
        self.clinician_group, _ = Group.objects.get_or_create(name=constants.CLINICIAN)
        self.admin_group, _ = Group.objects.get_or_create(name=constants.ADMIN)

        self.user = User.objects.create_user(
            email='user@email.com',
            phone_number = '+1234567811',
            first_name = 'John',
            last_name = 'Doe',
            password = 'Password?123',
            date_of_birth = datetime.date(1900, 1, 1),
        )
        self.user.groups.clear()

        self.valid_patient = User.objects.create_user(
            email='patient@email.com',
            phone_number='+1234567890',
            first_name='John',
            last_name='Doe',
            password='Password?123',
            date_of_birth=datetime.date(1900, 1, 1),
        )
        self.valid_patient.groups.add(self.patient_group)

        self.valid_clinician = User.objects.create_user(
            email='clinician@email.com',
            phone_number='+1234567891',
            first_name='John',
            last_name='Doe',
            password='Password?123',
            date_of_birth=datetime.date(1900, 1, 1),
        )
        self.valid_clinician.groups.add(self.clinician_group)

        self.valid_admin = User.objects.create_user(
            email='admin@email.com',
            phone_number='+1234567892',
            first_name='John',
            last_name='Doe',
            password='Password?123',
            date_of_birth=datetime.date(1900, 1, 1),
        )
        self.valid_admin.groups.add(self.admin_group)

        self.unregistered_google_user = User.objects.create_user(
            email='newgoogleuser@email.com',
            password='Password?123',
            first_name='John',
            last_name='Doe',
        )
        self.unregistered_google_user.groups.add(self.patient_group)

        self.registered_google_user = User.objects.create_user(
            email='googleuser@email.com',
            password='Password?123',
            phone_number='+1234567893',
            first_name='John',
            last_name='Doe',
            date_of_birth=datetime.date(1900, 1, 1),
        )
        self.registered_google_user.groups.add(self.patient_group)

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

    def test_admin_patient_login(self):
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
        self.assertRedirects(response, reverse("user:clinician:home"))

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


