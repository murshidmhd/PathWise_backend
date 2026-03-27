from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    AssessmentReportSerializer,
    AssessmentSerializer,
    QuestionSerializer,
    SubmitAssessmentSerializer,
)
from .services import (
    ServiceError,
    get_assessment_report,
    get_latest_assessment,
    list_questions,
    start_assessment,
    submit_assessment,
)


class AssessmentQuestionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        questions = list_questions()
        serializer = QuestionSerializer(questions, many=True)
        return Response(serializer.data)


class StartAssessmentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            assessment, created = start_assessment(request.user)
        except ServiceError as exc:
            return Response(exc.detail, status=exc.status_code)

        status_code = 201 if created else 200
        return Response(AssessmentSerializer(assessment).data, status=status_code)


class SubmitAssessmentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, assessment_id):
        serializer = SubmitAssessmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            assessment = submit_assessment(
                request.user,
                assessment_id,
                serializer.validated_data["answers"],
                serializer.validated_data.get("time_taken"),
            )
        except ServiceError as exc:
            return Response(exc.detail, status=exc.status_code)

        return Response(AssessmentSerializer(assessment).data, status=200)


class LatestAssessmentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            assessment = get_latest_assessment(request.user)
        except ServiceError as exc:
            return Response(exc.detail, status=exc.status_code)

        return Response(AssessmentSerializer(assessment).data)


class AssessmentReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, assessment_id):
        try:
            report = get_assessment_report(request.user, assessment_id)
        except ServiceError as exc:
            return Response(exc.detail, status=exc.status_code)

        return Response(AssessmentReportSerializer(report).data)
