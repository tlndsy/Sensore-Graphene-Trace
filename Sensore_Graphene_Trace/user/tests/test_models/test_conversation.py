import datetime

from django.test import TestCase
from django.db import IntegrityError

from user.models import User, Message, Conversation


class UserModelAndManagerTests(TestCase):
    def setUp(self):
        self.test_user_1 = User.objects.create_user(
            email="user@test.com",
            first_name="Test",
            last_name="User1",
            password="pass",
            date_of_birth=datetime.date(2000, 5, 5)
        )
        self.test_user_2 = User.objects.create_user(
            email="user2@test.com",
            first_name="Test",
            last_name="User2",
            password="pass",
            date_of_birth=datetime.date(2000, 5, 5)
        )

        self.conversation = Conversation.objects.create(subject="Test Conversation")
        self.conversation.participants.add(self.test_user_1)
        self.conversation.participants.add(self.test_user_2)

        self.test_message_1_data = {
            "conversation": self.conversation,
            "sender": self.test_user_1,
            "recipient": self.test_user_2,
            "content": "Hello, this is a test message."
        }
        self.test_message_2_data = {
            "conversation": self.conversation,
            "sender": self.test_user_2,
            "recipient": self.test_user_1,
            "content": "Hello, this is a test reply."
        }
