import datetime

from django.test import TestCase
from django.db import IntegrityError
from django.contrib.auth.models import Group

from user.models import User, Message, Conversation, PatientClinician
from Sensore_Graphene_Trace import global_constants as constants


class UserModelAndManagerTests(TestCase):
    def setUp(self):

        self.patient_group, _ = Group.objects.get_or_create(name=constants.PATIENT)
        self.clinician_group, _ = Group.objects.get_or_create(name=constants.CLINICIAN)
        self.admin_group, _ = Group.objects.get_or_create(name=constants.ADMIN)

        self.test_user_1 = User.objects.create_user(
            email="user@test.com",
            first_name="Test",
            last_name="User1",
            password="pass",
            date_of_birth=datetime.date(2000, 5, 5),
            role=constants.PATIENT
        )
        self.test_user_2 = User.objects.create_user(
            email="user2@test.com",
            first_name="Test",
            last_name="User2",
            password="pass",
            date_of_birth=datetime.date(2000, 5, 5),
            role=constants.CLINICIAN
        )
        PatientClinician.objects.create(patient=self.test_user_1, clinician=self.test_user_2)

        self.conversation = Conversation.objects.create_conversation(self.test_user_1, self.test_user_2, subject="Test Conversation")

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

    def test_create_message(self):
        message = Message.objects.create(**self.test_message_1_data)
        self.assertEqual(message.conversation, self.conversation)
        self.assertEqual(message.sender, self.test_user_1)
        self.assertEqual(message.recipient, self.test_user_2)
        self.assertEqual(message.content, "Hello, this is a test message.")
        self.assertIsNotNone(message.timestamp)

    def test_message_conversation_relationship(self):
        message1 = Message.objects.create(**self.test_message_1_data)
        message2 = Message.objects.create(**self.test_message_2_data)

        self.assertIn(message1, self.conversation.messages.all())
        self.assertIn(message2, self.conversation.messages.all())

    def test_message_sender_recipient_relationship(self):
        message1 = Message.objects.create(**self.test_message_1_data)
        message2 = Message.objects.create(**self.test_message_2_data)

        self.assertIn(message1, self.test_user_1.sent_messages.all())
        self.assertIn(message2, self.test_user_2.sent_messages.all())
        self.assertIn(message1, self.test_user_2.received_messages.all())
        self.assertIn(message2, self.test_user_1.received_messages.all())

    def test_message_timestamp_auto_now_add(self):
        message = Message.objects.create(**self.test_message_1_data)
        self.assertIsNotNone(message.timestamp)

    def test_attachment_path_generation(self):
        message = Message.objects.create(**self.test_message_1_data)
        path = message.attachment_path("dummy.jpg")
        expected_path = f"users/{self.test_user_1.id}/conversation_{self.conversation.id}/sent_items/dummy.jpg"
        self.assertEqual(path, expected_path)

    def test_conversation_cascade_delete(self):
        message = Message.objects.create(**self.test_message_1_data)
        self.conversation.delete()
        with self.assertRaises(Message.DoesNotExist):
            Message.objects.get(id=message.id)

    def test_sender_set_to_null_on_delete(self):
        message = Message.objects.create(**self.test_message_1_data)
        self.test_user_1.delete()
        message.refresh_from_db()
        self.assertIsNone(message.sender)

    def test_recipient_set_to_null_on_delete(self):
        message = Message.objects.create(**self.test_message_1_data)
        self.test_user_2.delete()
        message.refresh_from_db()
        self.assertIsNone(message.recipient)
