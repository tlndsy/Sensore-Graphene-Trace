from datetime import datetime

from django.test import TestCase
from django.db import IntegrityError

from user.models import Address


class UserModelAndManagerTests(TestCase):
    def setUp(self):

        self.address_data = {
            "first_line": "123 Test St",
            "second_line": "Testford",
            "town": "Test Town",
            "postal_code": "PE01 1AA",
        }

    def test_create_address(self):
        address = Address.objects.create(**self.address_data)
        self.assertEqual(address.first_line, self.address_data["first_line"])
        self.assertEqual(address.second_line, self.address_data["second_line"])
        self.assertEqual(address.town, self.address_data["town"])
        self.assertEqual(address.postal_code, self.address_data["postal_code"])
