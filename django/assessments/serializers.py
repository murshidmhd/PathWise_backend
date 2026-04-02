from rest_framework import serializers

from .models import Assessment, AssessmentReport, Question


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = [
            "id",
            "section",
            "sub_section",
            "question_text",
            "option_a",
            "option_b",
            "option_c",
            "option_d",
        ]


class AssessmentAnswerInputSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    selected_answer = serializers.ChoiceField(choices=["a", "b", "c", "d"])


class SubmitAssessmentSerializer(serializers.Serializer):
    answers = AssessmentAnswerInputSerializer(many=True)
    time_taken = serializers.IntegerField(required=False, min_value=0)


class AssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = [
            "id",
            "status",
            "attempt_number",
            "aptitude_score",
            "personality_score",
            "interest_score",
            "total_score",
            "time_taken",
            "created_at",
            "completed_at",
        ]


class   AssessmentReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentReport
        fields = [
            "id",
            "personality_type",
            "interest_areas",
            "recommended_careers",
            "strengths",
            "weaknesses",
            "report_text",
            "report_pdf_url",
            "created_at",
        ]
