from django.urls import reverse
from rest_framework.test import APITestCase

from .models import User
from counselors.models import CounselorProfile


class LoginCounselorStatusTests(APITestCase):
    def _create_counselor(self, email: str, approval_status: str, reason: str = ""):
        user = User.objects.create_user(
            email=email,
            password="StrongPass123!",
            role="counselor",
            first_name="Test",
            last_name="User",
        )
        user.is_active = True
        user.save()
        CounselorProfile.objects.create(
            user=user,
            full_name="Test Counselor",
            approval_status=approval_status,
            rejection_reason=reason,
        )
        return user

    def test_login_pending_returns_pending_code(self):
        self._create_counselor("pending@example.com", "pending")

        response = self.client.post(
            reverse("login"),
            {"email": "pending@example.com", "password": "StrongPass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data.get("code"), "PENDING_APPROVAL")

    def test_login_rejected_returns_rejected_code_and_reason(self):
        self._create_counselor(
            "rejected@example.com", "rejected", reason="Incomplete documents"
        )

        response = self.client.post(
            reverse("login"),
            {"email": "rejected@example.com", "password": "StrongPass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data.get("code"), "REJECTED")
        self.assertEqual(response.data.get("reason"), "Incomplete documents")

    def test_login_approved_returns_token_and_approved_code(self):
        self._create_counselor("approved@example.com", "approved")

        response = self.client.post(
            reverse("login"),
            {"email": "approved@example.com", "password": "StrongPass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("code"), "APPROVED")
        self.assertIn("access", response.data)
