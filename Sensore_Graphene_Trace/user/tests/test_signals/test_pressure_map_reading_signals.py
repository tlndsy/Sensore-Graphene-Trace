import csv
from datetime import timedelta, date
from io import StringIO

from django.core.files.uploadedfile import SimpleUploadedFile

from django.contrib.auth.models import Group

from user.models import PressureMapReading, ReadingEquipment, ProductInfo, User
from Sensore_Graphene_Trace import global_constants as constants

from django.test import TestCase
from django.core.files.base import ContentFile
from unittest.mock import patch


class PressureSignalTests(TestCase):

    def setUp(self):

        self.patient_group, _ = Group.objects.get_or_create(name=constants.PATIENT)
        self.clinician_group, _ = Group.objects.get_or_create(name=constants.CLINICIAN)
        self.admin_group, _ = Group.objects.get_or_create(name=constants.ADMIN)

        self.user = User.objects.create_user(
            email="testuser@test.com",
            first_name="Test",
            last_name="User1",
            password="password",
            date_of_birth=date(2000, 5, 5),
            role=constants.PATIENT
        )

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

        for _ in range(32*50):
            writer.writerow([100] * 32)

        dummy_csv_bytes = buffer.getvalue().encode('utf-8')

        self.uploaded_file = SimpleUploadedFile(
            "dummy.csv",
            dummy_csv_bytes,
            content_type="text/csv"
        )

    @patch("user.signals.process_pressure_csv")
    def test_signal_triggers_processing(self, mock_process):
        instance = PressureMapReading.objects.create(
            reading_equipment=self.reading_equipment,
            pressure_reading=self.uploaded_file,
            processed=False
        )

        self.assertTrue(mock_process.called)

    @patch("user.signals.process_pressure_csv")
    def test_signal_not_triggered_if_processed(self, mock_process):
        PressureMapReading.objects.create(
            reading_equipment=self.reading_equipment,
            pressure_reading=self.uploaded_file,
            processed=True
        )

        mock_process.assert_not_called()

    def test_full_processing_pipeline(self):
        instance = PressureMapReading.objects.create(
            reading_equipment=self.reading_equipment,
            pressure_reading=self.uploaded_file,
            processed=False
        )

        instance.refresh_from_db()

        self.assertTrue(instance.processed)
        self.assertIsNotNone(instance.metrics)

        content = instance.metrics.read().decode()
        self.assertIn("peak_pressure", content)

    def test_column_missmatch(self):
        buffer = StringIO()
        writer = csv.writer(buffer)
        for _ in range(32 * 50):
            writer.writerow([100] * 31)

        dummy_csv_bytes = buffer.getvalue().encode('utf-8')

        uploaded_file = SimpleUploadedFile(
            "dummy.csv",
            dummy_csv_bytes,
            content_type="text/csv"
        )

        with self.assertRaises(ValueError) as ctx:
            instance = PressureMapReading.objects.create(
                reading_equipment=self.reading_equipment,
                pressure_reading=uploaded_file,
                processed=False
            )

        self.assertIn(f"CSV must have {self.product_info.resolution_width} columns", str(ctx.exception))



    @patch("user.signals.process_pressure_csv")
    def test_signal_called_once(self, mock_process):
        instance = PressureMapReading.objects.create(
            reading_equipment=self.reading_equipment,
            pressure_reading=self.uploaded_file,
            processed=False
        )

        self.assertEqual(mock_process.call_count, 1)