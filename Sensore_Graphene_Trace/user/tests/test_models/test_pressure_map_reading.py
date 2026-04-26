import datetime

from django.test import TestCase
from django.db import IntegrityError

from user.models import ReadingEquipment, User, ProductInfo, PressureMapReading
from unittest.mock import patch

class PressureMapReadingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@test.com",
            first_name="Test",
            last_name="User",
            password="pass",
            date_of_birth=datetime.date(2000, 5, 5)
        )

        self.product_info = ProductInfo.objects.create(
            model="test model",
            manufacturer="test manufacturer",
            resolution_width=32,
            resolution_height=32,
            refresh_rate=15,
        )

        self.reading_equipment = ReadingEquipment.objects.create(
            product_info=self.product_info,
            serial_number="123456",
            user=self.user,
            custom_name="Test Device",
        )

        self.pressure_map_reading_data = {
            "reading_equipment": self.reading_equipment,
            "pressure_reading": "path/to/pressure/reading/file",
            "metrics": "path/to/metrics/file"
        }

    @patch("user.signals.process_pressure_csv")
    def test_create_pressure_map_reading(self, mock_process_pressure_csv):
        pressure_map_reading = PressureMapReading.objects.create(**self.pressure_map_reading_data)
        self.assertEqual(pressure_map_reading.reading_equipment, self.reading_equipment)
        self.assertEqual(pressure_map_reading.pressure_reading, "path/to/pressure/reading/file")
        self.assertEqual(pressure_map_reading.metrics, "path/to/metrics/file")

    @patch("user.signals.process_pressure_csv")
    def test_timestamp_auto_now_add(self, mock_process_pressure_csv):
        pressure_map_reading = PressureMapReading.objects.create(**self.pressure_map_reading_data)
        self.assertIsNotNone(pressure_map_reading.timestamp)

    @patch("user.signals.process_pressure_csv")
    def test_pressure_reading_path_generation(self, mock_process_pressure_csv):
        pressure_map_reading = PressureMapReading.objects.create(**self.pressure_map_reading_data)

        path = pressure_map_reading.pressure_reading_path("dummy.csv")
        expected_path = f"users/{self.reading_equipment.user.id}/pressure_maps/{pressure_map_reading.timestamp.strftime('%Y%m%d_%H%M%S')}/dummy.csv"

        self.assertEqual(path, expected_path)

    @patch("user.signals.process_pressure_csv")
    def test_reading_equipment_set_to_null_on_delete(self, mock_process_pressure_csv):
        pressure_map_reading = PressureMapReading.objects.create(**self.pressure_map_reading_data)
        self.reading_equipment.delete()
        pressure_map_reading.refresh_from_db()
        self.assertIsNone(pressure_map_reading.reading_equipment)
