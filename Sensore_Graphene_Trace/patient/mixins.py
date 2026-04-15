import datetime

from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, RequestFactory

from Sensore_Graphene_Trace import global_constants as constants
from user.mixins import GroupRequiredMixin
from user.models import User, ProductInfo, ReadingEquipment, PressureMapReading
from user.utils import notifications


class BasePatientMixin(GroupRequiredMixin):
    """
    Base patient access rules shared by all patient views.
    """

    # Login redirects
    login_url = "user:home"
    redirect_field_name = "next"

    # restrict which user groups can access
    group_required = [constants.PATIENT, constants.ADMIN]

    # restrict which apps are allowed
    allowed_apps = ["user"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["num_notifications"] = notifications.get_notification_count(self.request.user)
        return context

class PatientTestSetupMixin(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        # Patient
        self.patient_group, _ = Group.objects.get_or_create(name=constants.PATIENT)
        self.patient = User.objects.create_user(
            email='patient@email.com',
            phone_number='+1234567890',
            first_name='John',
            last_name='Doe',
            password='Password?123',
            date_of_birth=datetime.date(1900, 1, 1),
        )
        self.patient.groups.add(self.patient_group)

        self.product = ProductInfo.objects.create(
            model="Dave",
            manufacturer="Sensore",
            resolution_width=10,
            resolution_height=10,
            refresh_rate=60
        )

        self.equipment = ReadingEquipment.objects.create(
            product_info=self.product,
            serial_number="ABC123",
            user=self.patient
        )

        #  Pressure map reading and metrics
        self.metrics_file = SimpleUploadedFile(
            "metrics.json",
            b'{"test": "data"}',
            content_type="application/json"
        )

        self.reading = PressureMapReading.objects.create(
            reading_equipment=self.equipment,
            metrics=self.metrics_file
        )

    def create_csv_file(self, rows):
        content = "\n".join(",".join(str(v) for v in row) for row in rows)
        return SimpleUploadedFile(
            "pressure.csv",
            content.encode("utf-8"),
            content_type="text/csv"
        )