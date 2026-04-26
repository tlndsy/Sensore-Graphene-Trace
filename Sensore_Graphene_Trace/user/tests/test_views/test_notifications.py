import datetime

from django.test import TestCase, Client
from django.contrib.auth.models import Group
from django.urls import reverse

from user.models import User
import csv
from datetime import timedelta, date
from io import StringIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.utils import timezone

from user.models import Message, Conversation, PatientClinician, Report, PressureMapReading, ReadingEquipment, \
    ProductInfo
from user.utils.notifications import get_notification_count, get_notifications
from Sensore_Graphene_Trace import global_constants as constants



class NotificationsViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("user:notifications")

        self.patient_group, _ = Group.objects.get_or_create(name=constants.PATIENT)
        self.clinician_group, _ = Group.objects.get_or_create(name=constants.CLINICIAN)
        self.admin_group, _ = Group.objects.get_or_create(name=constants.ADMIN)

        self.user = User.objects.create_user(
            email="testuser@test.com",
            first_name="Test",
            last_name="User1",
            password="password",
            date_of_birth=date(2000, 5, 5),
            phone_number="+447700 900000",
            role=constants.PATIENT
        )
        self.user.groups.add(self.patient_group)

        self.sender = User.objects.create_user(
            email="otheruser@test.com",
            first_name="Test",
            last_name="User2",
            password="password",
            date_of_birth=date(2000, 5, 5),
            phone_number="+447700 900001",
            role = constants.CLINICIAN
        )
        self.user.groups.add(self.clinician_group)

        PatientClinician.objects.create(patient=self.user, clinician=self.sender)

        self.conversation = Conversation.objects.create_conversation(self.user, self.sender,subject="Test Conversation")

        self.product_info = ProductInfo.objects.create(
            model= "testmodel",
            manufacturer = "testmanufacturer",
            resolution_width = 32,
            resolution_height = 32,
            refresh_rate = 15,

        )

        self.reading_equipment = ReadingEquipment.objects.create(
            product_info=self.product_info,
            serial_number="test serial number",
            user=self.user,
        )

        # Create dummy csv
        buffer = StringIO()
        writer = csv.writer(buffer)

        for _ in range(60):
            writer.writerow([0] * 15)

        dummy_csv_bytes = buffer.getvalue().encode('utf-8')

        uploaded_file = SimpleUploadedFile(
            "dummy.csv",
            dummy_csv_bytes,
            content_type="text/csv"
        )


        self.pressure_reading = PressureMapReading.objects.create(
            reading_equipment=self.reading_equipment,
            pressure_reading=uploaded_file,
            processed=True,
        )

    def test_requires_login(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        #self.assertIn(reverse("user:home"), response.url)

    def test_allows_logged_in_user(self):
        self.client.login(email="testuser@test.com", password="password")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "user/user_notifications.html")
        self.assertEqual(response.context["num_notifications"], 0)

    def test_unread_message_included(self):
        msg = Message.objects.create(
            conversation=self.conversation,
            recipient=self.user,
            sender=self.sender,
            content="Hello world",
            read_receipt=False,
            timestamp=timezone.now()
        )

        self.client.login(email="testuser@test.com", password="password")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "user/user_notifications.html")
        self.assertEqual(response.context["num_notifications"], 1)
        self.assertIn("Today", response.context["notifications"])
        self.assertEqual(len(response.context["notifications"]["Today"]), 1)
        self.assertEqual(response.context["notifications"]["Today"][0]["type"], "message")
        self.assertIn("Unread Message From Test: Hello world", response.context["notifications"]["Today"][0]["text"])

    def test_read_message_excluded(self):
        Message.objects.create(
            conversation=self.conversation,
            recipient=self.user,
            sender=self.sender,
            content="Read message",
            read_receipt=True,
            timestamp=timezone.now()
        )

        self.client.login(email="testuser@test.com", password="password")

        response = self.client.get(self.url)

        self.assertEqual(len(response.context["notifications"]), 0)
        self.assertEqual(response.context["num_notifications"], 0)

    def test_pressure_alert_included(self):
        report = Report.objects.create(
            pressure_map_reading=self.pressure_reading,
            frame=1,
            pressure_alert=True,
            read_receipt=False,
        )

        self.client.login(email="testuser@test.com", password="password")

        response = self.client.get(self.url)

        notif = list(response.context["notifications"]["Today"])[0]
        self.assertEqual(notif["type"], "pressure_alert")
        self.assertIn("Pressure alert", notif["text"])

    def test_read_pressure_alert_excluded(self):
        report = Report.objects.create(
            pressure_map_reading=self.pressure_reading,
            frame=1,
            pressure_alert=True,
            read_receipt=True,
        )

        self.client.login(email="testuser@test.com", password="password")

        response = self.client.get(self.url)

        self.assertEqual(len(response.context["notifications"]), 0)
        self.assertEqual(response.context["num_notifications"], 0)

    def test_report_included(self):
        report = Report.objects.create(
            pressure_map_reading=self.pressure_reading,
            frame=1,
            pressure_alert=False,
            read_receipt=False,
        )

        self.client.login(email="testuser@test.com", password="password")

        response = self.client.get(self.url)

        notif = list(response.context["notifications"]["Today"])[0]
        self.assertEqual(notif["type"], "report")
        self.assertIn("Unread report", notif["text"])

    def test_read_report_excluded(self):
        report = Report.objects.create(
            pressure_map_reading=self.pressure_reading,
            frame=1,
            pressure_alert=False,
            read_receipt=True,
        )

        self.client.login(email="testuser@test.com", password="password")

        response = self.client.get(self.url)

        self.assertEqual(len(response.context["notifications"]), 0)
        self.assertEqual(response.context["num_notifications"], 0)
