from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User
from counselors.models import CounselorProfile
from students.models import StudentProfile


class AdminDashboardTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="Test1234!",
            role="admin",
            first_name="Admin",
            last_name="User",
            is_active=True,
            is_verified=True,
        )
        self.student_user = User.objects.create_user(
            email="student@example.com",
            password="Test1234!",
            role="student",
            first_name="Student",
            last_name="User",
            is_active=True,
            is_verified=True,
        )
        self.counselor_user = User.objects.create_user(
            email="counselor@example.com",
            password="Test1234!",
            role="counselor",
            first_name="Counselor",
            last_name="User",
            is_active=True,
            is_verified=True,
        )
        self.approved_counselor_user = User.objects.create_user(
            email="approved@example.com",
            password="Test1234!",
            role="counselor",
            first_name="Approved",
            last_name="Counselor",
            is_active=True,
            is_verified=True,
        )

        StudentProfile.objects.create(
            user=self.student_user,
            full_name="Student User",
            city="Kochi",
            state="Kerala",
        )
        CounselorProfile.objects.create(
            user=self.counselor_user,
            full_name="Pending Counselor",
            approval_status="pending",
        )
        CounselorProfile.objects.create(
            user=self.approved_counselor_user,
            full_name="Approved Counselor",
            approval_status="approved",
        )

    def test_admin_can_list_students_and_counselors(self):
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get("/api/admin-dashboard/users/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["students"]), 1)
        self.assertEqual(len(response.data["counselors"]), 2)
        self.assertEqual(response.data["students"][0]["email"], "student@example.com")

    def test_non_admin_cannot_access_admin_dashboard(self):
        self.client.force_authenticate(user=self.student_user)

        response = self.client.get("/api/admin-dashboard/users/")

        self.assertEqual(response.status_code, 403)

    def test_admin_can_list_pending_counselor_approvals(self):
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get("/api/admin-dashboard/counselors/pending/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["pending_counselors"]), 1)
        self.assertEqual(
            response.data["pending_counselors"][0]["email"], "counselor@example.com"
        )
