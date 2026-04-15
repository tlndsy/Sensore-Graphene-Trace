from unittest.mock import patch
from user.models import User, PasswordResetCode
from user.mixins import UserTestSetupMixin


class UserRequestPasswordResetViewTests(UserTestSetupMixin):
    @patch("user.views.send_mail")
    def test_request_password_reset_valid_email(self, mock_send_mail):
        response = self.client.post(self.url, {
            "form_type": "request_reset_code",
            "email": self.valid_patient.email
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enter Reset Code")
        self.assertTrue(PasswordResetCode.objects.filter(user=self.valid_patient).exists())
        mock_send_mail.assert_called_once()

    def test_request_password_reset_invalid_email(self):
        response = self.client.post(self.url, {
            "form_type": "request_reset_code",
            "email": "invalid@email.com"
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No account with that email.")

    def test_reset_code_is_six_digits(self):
        self.client.post(self.url, {
            "form_type": "request_reset_code",
            "email": self.valid_patient.email
        })
        reset = PasswordResetCode.objects.get(user=self.valid_patient)
        self.assertEqual(len(reset.code), 6)
