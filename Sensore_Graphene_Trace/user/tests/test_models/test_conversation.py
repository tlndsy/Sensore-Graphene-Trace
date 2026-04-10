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


    def create_conversation(self, participants):
        conversation = Conversation.objects.create_conversation(subject="Test Conversation", participants=participants)
        return conversation

    def test_valid_conversation_with_patient_clinician_relationship(self):
        conversation = self.create_conversation([self.test_patient_1, self.test_clinician_1])

        # Should not raise
        conversation.full_clean()

        self.assertIn(self.test_patient_1, conversation.participants.all())
        self.assertIn(self.test_clinician_1, conversation.participants.all())

    def test_invalid_conversation_more_than_two_participants(self):
        with self.assertRaises(ValidationError) as ctx:
            conversation = self.create_conversation([self.test_patient_1, self.test_clinician_1,  self.test_patient_2])

        self.assertIn("exactly 2 participants", str(ctx.exception))

    def test_invalid_conversation_without_relationship(self):
        with self.assertRaises(ValidationError) as ctx:
            conversation = self.create_conversation([self.test_patient_1, self.test_clinician_2])

        self.assertIn("valid patient-clinician relationship.", str(ctx.exception))

    def test_invalid_conversation_same_user(self):
        with self.assertRaises(ValidationError) as ctx:
            conversation = self.create_conversation([self.test_patient_1, self.test_patient_1])

        self.assertIn("Users must be different.", str(ctx.exception))


    def test_valid_conversation_with_admin(self):

        conversation = self.create_conversation([self.test_patient_1, self.test_admin])

        # Should not raise
        conversation.full_clean()

        self.assertIn(self.test_patient_1, conversation.participants.all())
        self.assertIn(self.test_admin, conversation.participants.all())

    def test_duplicate_conversation_not_created1(self):
        conversation1 = self.create_conversation([self.test_patient_1, self.test_clinician_1])
        conversation2 = self.create_conversation([self.test_patient_1, self.test_clinician_1])

        self.assertEqual(conversation1, conversation2)

    def test_duplicate_conversation_reversed_participants_not_created(self):
        conversation1 = self.create_conversation([self.test_patient_1, self.test_clinician_1])
        conversation2 = self.create_conversation([self.test_clinician_1, self.test_patient_1])

        self.assertEqual(conversation1, conversation2)

    def test_conversation_manager_enforced(self):
        with self.assertRaises(RuntimeError) as ctx:
            conversation = Conversation.objects.create(subject="Invalid Conversation")
            conversation.participants.add(self.test_patient_1)
            conversation.participants.add(self.test_clinician_1)
            conversation.full_clean()

        self.assertIn("Use Conversation.objects.create_conversation() to create conversations", str(ctx.exception))




