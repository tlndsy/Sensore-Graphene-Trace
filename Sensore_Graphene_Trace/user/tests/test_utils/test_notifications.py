import datetime

from django.test import TestCase
from django.contrib.auth import get_user_model

from user.models import Message, Conversation
from user.utils.notifications import get_notification_count, get_notifications

User = get_user_model()


class NotificationUtilsTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@test.com",
            first_name="Test",
            last_name="User1",
            password="password",
            date_of_birth=datetime.date(2000, 5, 5)
        )

        self.other_user = User.objects.create_user(
            email="otheruser@test.com",
            first_name="Test",
            last_name="User2",
            password="password",
            date_of_birth=datetime.date(2000, 5, 5)
        )

        self.conversation = Conversation.objects.create(
            subject="Test Conversation"
        )
        self.conversation.participants.add(self.user)
        self.conversation.participants.add(self.other_user)

        # Create messages for self.user
        self.unread_msg1 = Message.objects.create(
            conversation=self.conversation,
            sender=self.other_user,
            recipient=self.user,
            content="Unread message 1",
            read_receipt=False
        )

        self.unread_msg2 = Message.objects.create(
            conversation=self.conversation,
            sender=self.other_user,
            recipient=self.user,
            content="Unread message 2",
            read_receipt=False
        )

        self.read_msg = Message.objects.create(
            conversation=self.conversation,
            sender=self.other_user,
            recipient=self.user,
            content="Read message",
            read_receipt=True
        )

        # Message for another user (should not be counted)
        Message.objects.create(
            conversation=self.conversation,
            sender=self.user,
            recipient=self.other_user,
            content="Other user's message",
            read_receipt=False
        )

    def test_get_notification_count_only_counts_unread(self):
        count = get_notification_count(self.user)
        self.assertEqual(count, 2)

    def test_get_notification_count_returns_zero_when_no_messages(self):
        new_user = User.objects.create_user(
            email="nouser@test.com",
            first_name="Test",
            last_name="User3",
            password="password",
            date_of_birth=datetime.date(2000, 5, 5)
        )
        count = get_notification_count(new_user)
        self.assertEqual(count, 0)

    def test_get_notifications_returns_only_unread_messages(self):
        notifications = get_notifications(self.user)
        messages = notifications["messages"]

        self.assertEqual(messages.count(), 2)

        for msg in messages:
            self.assertFalse(msg.read_receipt)
            self.assertEqual(msg.recipient, self.user)

    def test_get_notifications_orders_by_timestamp_desc(self):
        notifications = get_notifications(self.user)
        messages = list(notifications["messages"])

        self.assertEqual(len(messages), 2)
        self.assertGreaterEqual(
            messages[0].timestamp,
            messages[1].timestamp
        )
