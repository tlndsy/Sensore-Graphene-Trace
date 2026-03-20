from django.test import TestCase, RequestFactory
from django.http import Http404
from django.contrib.auth.models import Permission, Group
from django.views.generic import View, ListView, DetailView
from django.apps import apps

from unittest.mock import patch

from user.models import User
from administrator.mixins import BaseGenericModelMixin
from Sensore_Graphene_Trace import global_constants as constants


# Dummy model for testing (use an existing model in your "user" app)
UserModel = apps.get_model("user", "User")

# Dummy single object view for testing
class TestDetailView(BaseGenericModelMixin, DetailView):
    permission_action = None
    allowed_apps = ["user"]

    def get(self, request, *args, **kwargs):
        return None

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs)

# Dummy multi-object view for testing
class TestListView(BaseGenericModelMixin, ListView):
    permission_action = None
    allowed_apps = ["user"]

    def get(self, request, *args, **kwargs):
        return None

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs)



class BaseGenericModelMixinTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(email="testuser@test.com", password="pass", date_of_birth="2000-01-01")

        # Create admin group
        self.admin_group = Group.objects.create(name=constants.ADMIN)
        self.user.groups.add(self.admin_group)

        self.request = self.factory.get("/")
        self.request.user = self.user

        self.detailView = TestDetailView()
        self.detailView.request = self.request
        self.detailView.kwargs = {
            "app_label": "user",
            "model_name": "User",
        }

        self.listView = TestListView()
        self.listView.request = self.request
        self.listView.kwargs = {
            "app_label": "user",
            "model_name": "User",
        }

    # -------------------------
    # get_model
    # -------------------------
    def test_get_model_success(self):
        detail_model = self.detailView.get_model()
        list_model = self.listView.get_model()
        self.assertEqual(detail_model, UserModel)
        self.assertEqual(list_model, UserModel)

    def test_get_model_disallowed_app(self):
        self.listView.allowed_apps = ["other_app"]
        with self.assertRaises(Http404):
            self.listView.get_model()
        self.detailView.allowed_apps = ["other_app"]
        with self.assertRaises(Http404):
            self.detailView.get_model()

    # -------------------------
    # dispatch
    # -------------------------
    def test_dispatch_sets_model(self):
        _ = self.listView.dispatch(self.request, **self.listView.kwargs)
        _ = self.detailView.dispatch(self.request, **self.listView.kwargs)
        self.assertEqual(self.detailView.model, UserModel)
        self.assertEqual(self.listView.model, UserModel)

    # -------------------------
    # test_func
    # -------------------------
    @patch("administrator.mixins.BaseAdminMixin.test_func", return_value=True)
    def test_test_func_no_permission_required(self, mock_super):
        self.detailView.model = UserModel
        self.detailView.permission_action = None

        self.listView.model = UserModel
        self.listView.permission_action = None

        self.assertTrue(self.detailView.test_func())
        self.assertTrue(self.listView.test_func())

    @patch("administrator.mixins.BaseAdminMixin.test_func", return_value=False)
    def test_test_func_fails_if_base_admin_fails(self, mock_super):
        self.detailView.model = UserModel
        self.listView.model = UserModel

        self.assertFalse(self.detailView.test_func())
        self.assertFalse(self.listView.test_func())

    @patch("administrator.mixins.BaseAdminMixin.test_func", return_value=True)
    def test_test_func_with_permission(self, mock_super):
        self.detailView.model = UserModel
        self.detailView.permission_action = "view"

        self.listView.model = UserModel
        self.listView.permission_action = "view"

        perm_codename = f"view_{UserModel._meta.model_name}"
        permission = Permission.objects.get(codename=perm_codename)
        self.user.user_permissions.add(permission)

        self.assertTrue(self.detailView.test_func())
        self.assertTrue(self.listView.test_func())

    @patch("administrator.mixins.BaseAdminMixin.test_func", return_value=True)
    def test_test_func_without_permission(self, mock_super):
        self.detailView.model = UserModel
        self.detailView.permission_action = "view"

        self.listView.model = UserModel
        self.listView.permission_action = "view"

        self.assertFalse(self.detailView.test_func())
        self.assertFalse(self.listView.test_func())

    # -------------------------
    # queryset
    # -------------------------
    def test_get_queryset(self):
        self.listView.model = UserModel
        qs = self.listView.get_queryset()
        self.assertEqual(list(qs), list(UserModel.objects.all()))

    # -------------------------
    # context
    # -------------------------
    @patch("administrator.mixins.notifications.get_notification_count", return_value=5)
    def test_get_context_data_list_view(self, mock_notifications):
        self.listView.model = UserModel
        self.listView.object_list = self.listView.get_queryset()

        context = self.listView.get_context_data()

        self.assertEqual(context["model_verbose_name"], UserModel._meta.verbose_name.title())
        self.assertEqual(context["app_label"], "user")
        self.assertEqual(context["model_name"], "user")
        self.assertEqual(context["num_notifications"], 5)

    @patch("administrator.mixins.notifications.get_notification_count", return_value=5)
    def test_get_context_data_detail_view(self, mock_notifications):
        self.detailView.model = UserModel
        self.detailView.object = UserModel.objects.first()

        context = self.detailView.get_context_data()

        self.assertEqual(context["model_verbose_name"], UserModel._meta.verbose_name.title())
        self.assertEqual(context["app_label"], "user")
        self.assertEqual(context["model_name"], "user")
        self.assertEqual(context["num_notifications"], 5)