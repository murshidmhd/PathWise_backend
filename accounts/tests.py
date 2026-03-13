from django.test import TestCase
from rest_framework.test import APIClient

from unittest.mock import patch


class AuthTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    @patch("accounts.views.is_valid_recaptcha", return_value=True)
    def test_student_registration(self, mock_recaptcha):
        response = self.client.post(
            "/api/auth/register/",
            {
                "email": "test@example.com",
                "password": "Test1234!",
                "confirm_password": "Test1234!",
                "role": "student",
                "first_name": "Test",
                "last_name": "User",
            },
        )
        print(response.data)  # add this line
        self.assertEqual(response.status_code, 200)

        # send POST to /api/auth/register/
        # check status code is 200
        # check OTP email was sent

    def test_password_mismatch(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "email": "test@example.com",
                "password": "Test1234!",
                "confirm_password": "Wrong1234!",
                "role": "student",
                "first_name": "Test",
                "last_name": "User",
            },
        )
        self.assertEqual(response.status_code, 400)
