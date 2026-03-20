from datetime import datetime

from django.test import TestCase
from django.db import IntegrityError

from user.models import ReadingEquipment, User, ProductInfo


class UserModelAndManagerTests(TestCase):
    def setUp(self):

        self.user = User.objects.create_user(
            email="user@test.com", password="pass", date_of_birth=datetime.now()
        )

        self.product_info = ProductInfo.objects.create(
            model="test model",
            manufacturer="test manufacturer",
            resolution_width=32,
            resolution_height=32,
            refresh_rate=15,
        )

        self.reading_equipment_data = {
            "product_info": self.product_info,
            "serial_number": "123456",
            "user": self.user,
            "custom_name": "Test Device",
        }

    def test_create_reading_equipment(self):
        reading_equipment = ReadingEquipment.objects.create(**self.reading_equipment_data)
        self.assertEqual(reading_equipment.product_info, self.product_info)
        self.assertEqual(reading_equipment.serial_number, "123456")
        self.assertEqual(reading_equipment.user, self.user)
        self.assertEqual(reading_equipment.custom_name, "Test Device")

    def test_serial_number_uniqueness(self):
        ReadingEquipment.objects.create(**self.reading_equipment_data)
        with self.assertRaises(IntegrityError):
            ReadingEquipment.objects.create(**self.reading_equipment_data)

    def test_default_device_name(self):
        reading_equipment = ReadingEquipment.objects.create(
            product_info=self.product_info,
            serial_number="654321",
            user=self.user,
        )
        expected_default_name = f"{self.product_info.model} - 654321"
        self.assertEqual(reading_equipment.custom_name, expected_default_name)

    def test_user_cascade_delete(self):
        reading_equipment = ReadingEquipment.objects.create(**self.reading_equipment_data)
        self.user.delete()
        with self.assertRaises(ReadingEquipment.DoesNotExist):
            ReadingEquipment.objects.get(id=reading_equipment.id)