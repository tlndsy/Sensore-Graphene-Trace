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


class UserLogoutViewTests(UserTestSetupMixin):
    def test_logout_redirects_to_home(self):
        self.client.login(email=self.valid_patient.email, password='Password?123')
        response = self.client.get(self.logout_url)
        self.assertRedirects(response, self.url)

    def test_user_is_logged_out_after_logout(self):
        self.client.login(email=self.valid_patient.email, password='Password?123')
        self.client.get(self.logout_url)
        response = self.client.get(self.url)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_session_is_cleared_on_logout(self):
        self.client.login(email=self.valid_patient.email, password='Password?123')
        session = self.client.session
        session["test_key"] = "test_value"
        session.save()
        self.client.get(self.logout_url)
        session = self.client.session
        self.assertNotIn("test_key", session)
