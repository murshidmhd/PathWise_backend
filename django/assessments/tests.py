# from django.test import TestCase
# from rest_framework.test import APIClient

# from accounts.models import User
# from students.models import StudentProfile

# from .models import Assessment, AssessmentReport, Question


# class AssessmentEndpointTests(TestCase):
#     def setUp(self):
#         self.client = APIClient()
#         self.user = User.objects.create_user(
#             email="student@example.com",
#             password="Test1234",
#             role="student",
#             first_name="Test",
#             last_name="Student",
#             is_active=True,
#             is_verified=True,
#         )
#         self.student = StudentProfile.objects.create(
#             user=self.user,
#             full_name="Test Student",
#         )
#         self.client.force_authenticate(user=self.user)

#     def create_question(self, **overrides):
#         data = {
#             "section": "aptitude",
#             "sub_section": "logical",
#             "question_text": "What is 2 + 2?",
#             "option_a": "3",
#             "option_b": "4",
#             "option_c": "5",
#             "option_d": "6",
#             "correct_answer": "b",
#             "marks": 1,
#         }
#         data.update(overrides)
#         return Question.objects.create(**data)

#     def test_start_creates_first_assessment(self):
#         response = self.client.post("/api/assessments/start/", {})

#         self.assertEqual(response.status_code, 201)
#         self.assertEqual(response.data["status"], "started")
#         self.assertEqual(Assessment.objects.filter(student=self.student).count(), 1)

#     def test_start_returns_existing_started_assessment(self):
#         assessment = Assessment.objects.create(student=self.student, status="started")

#         response = self.client.post("/api/assessments/start/", {})

#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(response.data["id"], assessment.id)
#         self.assertEqual(Assessment.objects.filter(student=self.student).count(), 1)

#     def test_start_rejects_second_assessment_after_completion(self):
#         assessment = Assessment.objects.create(student=self.student, status="completed")

#         response = self.client.post("/api/assessments/start/", {})

#         self.assertEqual(response.status_code, 409)
#         self.assertEqual(response.data["assessment_id"], assessment.id)
#         self.assertEqual(Assessment.objects.filter(student=self.student).count(), 1)

#     def test_latest_returns_existing_assessment(self):
#         assessment = Assessment.objects.create(student=self.student, status="started")

#         response = self.client.get("/api/assessments/latest/")

#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(response.data["id"], assessment.id)

#     def test_submit_requires_all_questions(self):
#         question_one = self.create_question(question_text="Question one?")
#         self.create_question(question_text="Question two?")
#         assessment = Assessment.objects.create(student=self.student, status="started")

#         response = self.client.post(
#             f"/api/assessments/{assessment.id}/submit/",
#             {
#                 "answers": [
#                     {
#                         "question_id": question_one.id,
#                         "selected_answer": "b",
#                     }
#                 ]
#             },
#             format="json",
#         )

#         self.assertEqual(response.status_code, 400)
#         self.assertEqual(
#             response.data["message"],
#             "All assessment questions must be answered before submission.",
#         )
#         assessment.refresh_from_db()
#         self.assertEqual(assessment.status, "started")

#     def test_submit_completes_assessment_and_generates_report(self):
#         question_one = self.create_question(question_text="Question one?")
#         question_two = self.create_question(
#             question_text="Question two?",
#             correct_answer="a",
#         )
#         assessment = Assessment.objects.create(student=self.student, status="started")

#         response = self.client.post(
#             f"/api/assessments/{assessment.id}/submit/",
#             {
#                 "answers": [
#                     {
#                         "question_id": question_one.id,
#                         "selected_answer": "b",
#                     },
#                     {
#                         "question_id": question_two.id,
#                         "selected_answer": "a",
#                     },
#                 ],
#                 "time_taken": 120,
#             },
#             format="json",
#         )

#         self.assertEqual(response.status_code, 200)
#         assessment.refresh_from_db()
#         self.student.refresh_from_db()
#         self.assertEqual(assessment.status, "completed")
#         self.assertEqual(assessment.total_score, 2)
#         self.assertEqual(assessment.time_taken, 120)
#         self.assertTrue(self.student.assessment_taken)
#         self.assertTrue(AssessmentReport.objects.filter(assessment=assessment).exists())

#     def test_report_requires_completed_assessment(self):
#         assessment = Assessment.objects.create(student=self.student, status="started")

#         response = self.client.get(f"/api/assessments/{assessment.id}/report/")

#         self.assertEqual(response.status_code, 400)
#         self.assertEqual(
#             response.data["message"],
#             "Assessment report is only available after completion.",
#         )

#     def test_report_returns_completed_assessment_report(self):
#         assessment = Assessment.objects.create(student=self.student, status="completed")
#         AssessmentReport.objects.create(
#             assessment=assessment,
#             student=self.student,
#             personality_type="Investigative",
#             interest_areas=["data"],
#             recommended_careers=["Data Scientist"],
#             strengths=["analytical thinking"],
#             weaknesses=["fast social situations"],
#             report_text="A good fit for analytical work.",
#         )

#         response = self.client.get(f"/api/assessments/{assessment.id}/report/")

#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(response.data["personality_type"], "Investigative")
