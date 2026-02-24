from django.urls import path
from .views import GenericCreateView, GenericListView, GenericUpdateView, GenericDeleteView, AdminHomeView

app_name = 'administrator'

urlpatterns = [
    path("", AdminHomeView.as_view(), name="home"),
    path(
        "create/<str:app_label>/<str:model_name>/",
        GenericCreateView.as_view(),
        name="generic_create",
    ),
    path(
        "list/<str:app_label>/<str:model_name>/",
        GenericListView.as_view(),
        name="generic_list",
    ),
    path(
        "update/<str:app_label>/<str:model_name>/<str:pk>/",
        GenericUpdateView.as_view(),
        name="generic_update",
    ),
    path(
        "delete/<str:app_label>/<str:model_name>/<str:pk>/",
        GenericDeleteView.as_view(),
        name="generic_delete",
    ),
]