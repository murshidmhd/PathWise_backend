from django.test import TestCase
from rest_framework.test import APIClient


class AuthTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_student_registration(self):

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
        self.assertEqual(response.status_code, 200)

        # send POST to /api/auth/register/
        # check status code is 200
        # check OTP email was sent
        pass
