import datetime

from django.core.exceptions import ValidationError
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

        self.test_patient_1 = User.objects.create_user(
            email="patient1@test.com",
            first_name="Test",
            last_name="User1",
            password="pass",
            date_of_birth=datetime.date(2000, 5, 5),
            role = constants.PATIENT,
        )

        self.test_patient_2 = User.objects.create_user(
            email="patient2@test.com",
            first_name="Test",
            last_name="User1",
            password="pass",
            date_of_birth=datetime.date(2000, 5, 5),
            role = constants.PATIENT,
        )

        self.test_clinician_1 = User.objects.create_user(
            email="clinician1@test.com",
            first_name="Test",
            last_name="User2",
            password="pass",
            date_of_birth=datetime.date(2000, 5, 5),
            role = constants.CLINICIAN,
        )

        self.test_clinician_2 = User.objects.create_user(
            email="clinician2@test.com",
            first_name="Test",
            last_name="User2",
            password="pass",
            date_of_birth=datetime.date(2000, 5, 5),
            role = constants.CLINICIAN,
        )

        self.test_admin = User.objects.create_user(
            email="admin@test.com",
            first_name="Test",
            last_name="User2",
            password="pass",
            date_of_birth=datetime.date(2000, 5, 5),
            role=constants.ADMIN,
        )

        PatientClinician.objects.create(patient=self.test_patient_1, clinician=self.test_clinician_1)
        PatientClinician.objects.create(patient=self.test_patient_2, clinician=self.test_clinician_2)


    def create_conversation(self, user1, user2):
        conversation = Conversation.objects.create_conversation(user1, user2, subject="Test Conversation")
        return conversation

    def test_valid_conversation_with_patient_clinician_relationship(self):
        conversation = self.create_conversation(self.test_patient_1, self.test_clinician_1)

        # Should not raise
        conversation.full_clean()

        self.assertIn(self.test_patient_1, conversation.participants.all())
        self.assertIn(self.test_clinician_1, conversation.participants.all())

    def test_invalid_conversation_without_relationship(self):
        with self.assertRaises(ValidationError) as ctx:
            conversation = self.create_conversation(self.test_patient_1, self.test_clinician_2)

        self.assertIn("valid patient-clinician relationship.", str(ctx.exception))

    def test_invalid_conversation_between_two_patients(self):
        with self.assertRaises(ValidationError) as ctx:
            conversation = self.create_conversation(self.test_patient_1, self.test_patient_2)

        self.assertIn("valid patient-clinician relationship.", str(ctx.exception))

    def test_invalid_conversation_same_user(self):
        with self.assertRaises(ValidationError) as ctx:
            conversation = self.create_conversation(self.test_patient_1, self.test_patient_1)

        self.assertIn("Users must be different.", str(ctx.exception))


    def test_valid_conversation_with_admin(self):

        conversation = self.create_conversation(self.test_patient_1, self.test_admin)

        # Should not raise
        conversation.full_clean()

        self.assertIn(self.test_patient_1, conversation.participants.all())
        self.assertIn(self.test_admin, conversation.participants.all())

    def test_no_duplicate_conversations(self):
        convo1 = Conversation.objects.create_conversation(self.test_patient_1, self.test_clinician_1)
        convo2 = Conversation.objects.create_conversation(self.test_patient_1, self.test_clinician_1)

        self.assertEqual(convo1.id, convo2.id)
        self.assertEqual(Conversation.objects.count(), 1)

    def test_conversation_manager_enforced(self):

        with self.assertRaises(RuntimeError) as ctx:
            convo1 = Conversation.objects.create(subject="Test Conversation")
            convo1.participants.set([self.test_patient_1, self.test_clinician_1])

        self.assertIn("Use Conversation.objects.create_conversation()", str(ctx.exception))

    def test_last_message_updates(self):
        conversation = self.create_conversation(self.test_patient_1, self.test_clinician_1)

        message1 = Message.objects.create(
            conversation=conversation,
            sender=self.test_patient_1,
            recipient=self.test_clinician_1,
            content="First message"
        )

        self.assertEqual(conversation.last_message, message1)

        message2 = Message.objects.create(
            conversation=conversation,
            sender=self.test_clinician_1,
            recipient=self.test_patient_1,
            content="Reply message"
        )

        conversation.refresh_from_db()
        self.assertEqual(conversation.last_message, message2)

    def test_updated_at_auto_now(self):
        conversation = self.create_conversation(self.test_patient_1, self.test_clinician_1)
        old_updated_at = conversation.updated_at

        # Simulate a wait to ensure timestamp difference
        import time
        time.sleep(1)

        message = Message.objects.create(
            conversation=conversation,
            sender=self.test_patient_1,
            recipient=self.test_clinician_1,
            content="Testing updated_at"
        )

        conversation.refresh_from_db()
        self.assertGreater(conversation.updated_at, old_updated_at)