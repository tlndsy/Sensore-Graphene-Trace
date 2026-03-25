import datetime

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import Group, AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.views import View

from Sensore_Graphene_Trace import global_constants as constants
from user.mixins import GroupRequiredMixin
from user.models import User


class TestView(GroupRequiredMixin, View):
    group_required = constants.CLINICIAN

    def get(self, request):
        return HttpResponse("OK")


class GroupRequiredMixinTests(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

        self.group, _ = Group.objects.get_or_create(name=constants.CLINICIAN)

        self.user = User.objects.create_user(
            email="test@test.com",
            first_name="Test",
            last_name="User2",
            password="pass",
            date_of_birth=datetime.date(2000, 5, 5)
        )

        self.superuser = User.objects.create_superuser(
            email="admin@test.com",
            first_name="Admin",
            last_name="User",
            password="pass",
            date_of_birth=datetime.date(2000, 5, 5)
        )

    def get_view(self, user):
        request = self.factory.get("/")
        request.user = user
        view = TestView()
        view.request = request
        return view

    def test_unauthenticated_user_fails_test_func(self):
        view = self.get_view(AnonymousUser())
        self.assertFalse(view.test_func())

    def test_superuser_passes_test_func(self):
        view = self.get_view(self.superuser)
        self.assertTrue(view.test_func())

    def test_user_in_required_group_passes(self):
        self.user.groups.add(self.group)
        view = self.get_view(self.user)

        self.assertTrue(view.test_func())

    def test_user_not_in_group_fails(self):
        self.user.groups.clear()
        view = self.get_view(self.user)
        self.assertFalse(view.test_func())

    def test_group_required_as_list(self):
        class ListGroupView(TestView):
            group_required = [constants.CLINICIAN, constants.ADMIN]

        self.user.groups.add(self.group)

        request = self.factory.get("/")
        request.user = self.user

        view = ListGroupView()
        view.request = request

        self.assertTrue(view.test_func())

    def test_handle_no_permission_authenticated_user(self):
        view = self.get_view(self.user)

        with self.assertRaises(PermissionDenied):
            view.handle_no_permission()

    def test_handle_no_permission_anonymous_user(self):
        request = self.factory.get("/")
        request.user = AnonymousUser()

        view = TestView()
        view.request = request

        response = view.handle_no_permission()

        # 302 redirect
        self.assertEqual(response.status_code, 302)
