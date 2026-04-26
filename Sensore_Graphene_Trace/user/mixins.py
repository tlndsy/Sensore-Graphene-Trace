from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
import datetime
from django.test import TestCase, Client
from django.contrib.auth.models import Group
from django.urls import reverse
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
from Sensore_Graphene_Trace import global_constants as constants
from user.models import User


class GroupRequiredMixin(UserPassesTestMixin):
    group_required = None

    # Override the test_func method to check if the user belongs to the required group(s)
    def test_func(self):
        user = self.request.user

        if not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        if not self.group_required:
            return True

        if isinstance(self.group_required, str):
            groups = [self.group_required]
        else:
            groups = self.group_required

        return user.groups.filter(name__in=groups).exists()

    # Raise 403 Forbidden if the user does not have permission to access the page
    def handle_no_permission(self):
        # if user is not logged in, redirect to login page
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()

        raise PermissionDenied("You do not have permission to access this page.")


# Creates fake users for the unit tests
class UserTestSetupMixin(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('user:home')
        self.logout_url = reverse('user:logout_user')

        # Google setup
        site = Site.objects.get_current()
        social_app = SocialApp.objects.create(
            provider='google',
            name='Google',
            client_id='test-client-id',
            secret='test-secret'
        )
        social_app.sites.add(site)

        # Groups
        self.patient_group, _ = Group.objects.get_or_create(name=constants.PATIENT)
        self.clinician_group, _ = Group.objects.get_or_create(name=constants.CLINICIAN)
        self.admin_group, _ = Group.objects.get_or_create(name=constants.ADMIN)

        # Users
        self.user = User.objects.create_user(
            email='user@email.com',
            phone_number='+1234567811',
            first_name='John',
            last_name='Doe',
            password='Password?123',
            date_of_birth=datetime.date(1900, 1, 1),
        )
        self.user.groups.clear()

        # Patient
        self.valid_patient = User.objects.create_user(
            email='patient@email.com',
            phone_number='+1234567890',
            first_name='John',
            last_name='Doe',
            password='Password?123',
            date_of_birth=datetime.date(1900, 1, 1),
        )
        self.valid_patient.groups.add(self.patient_group)

        # Clinician
        self.valid_clinician = User.objects.create_user(
            email='clinician@email.com',
            phone_number='+1234567891',
            first_name='John',
            last_name='Doe',
            password='Password?123',
            date_of_birth=datetime.date(1900, 1, 1),
        )
        self.valid_clinician.groups.add(self.clinician_group)

        # Admin
        self.valid_admin = User.objects.create_user(
            email='admin@email.com',
            phone_number='+1234567892',
            first_name='John',
            last_name='Doe',
            password='Password?123',
            date_of_birth=datetime.date(1900, 1, 1),
        )
        self.valid_admin.groups.add(self.admin_group)

        # Unregistered google user
        self.unregistered_google_user = User.objects.create_user(
            email='newgoogleuser@email.com',
            password='Password?123',
            first_name='John',
            last_name='Doe',
        )
        self.unregistered_google_user.groups.add(self.patient_group)

        # Registered google user
        self.registered_google_user = User.objects.create_user(
            email='googleuser@email.com',
            password='Password?123',
            phone_number='+1234567893',
            first_name='John',
            last_name='Doe',
            date_of_birth=datetime.date(1900, 1, 1),
        )
        self.registered_google_user.groups.add(self.patient_group)
