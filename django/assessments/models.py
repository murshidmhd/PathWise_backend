from django.db import models


class Question(models.Model):

    SECTION_CHOICES = [
        ('aptitude', 'Aptitude'),
        ('personality', 'Personality'),
        ('interest', 'Interest'),
    ]

    SUB_SECTION_CHOICES = [
        ('logical', 'Logical'),
        ('numerical', 'Numerical'),
        ('verbal', 'Verbal'),
        ('spatial', 'Spatial'),
    ]

    RIASEC_CHOICES = [
        ('R', 'Realistic'),
        ('I', 'Investigative'),
        ('A', 'Artistic'),
        ('S', 'Social'),
        ('E', 'Enterprising'),
        ('C', 'Conventional'),
    ]

    section       = models.CharField(max_length=20, choices=SECTION_CHOICES)
    sub_section   = models.CharField(max_length=50, choices=SUB_SECTION_CHOICES, null=True, blank=True)
    question_text = models.TextField()

    option_a = models.CharField(max_length=500, null=True, blank=True)
    option_b = models.CharField(max_length=500, null=True, blank=True)
    option_c = models.CharField(max_length=500, null=True, blank=True)
    option_d = models.CharField(max_length=500, null=True, blank=True)

    option_a_type = models.CharField(max_length=10, choices=RIASEC_CHOICES, null=True, blank=True)
    option_b_type = models.CharField(max_length=10, choices=RIASEC_CHOICES, null=True, blank=True)
    option_c_type = models.CharField(max_length=10, choices=RIASEC_CHOICES, null=True, blank=True)
    option_d_type = models.CharField(max_length=10, choices=RIASEC_CHOICES, null=True, blank=True)

    correct_answer = models.CharField(max_length=1, null=True, blank=True)
    marks          = models.IntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['section', 'sub_section']

    def __str__(self):
        return f"[{self.section}] {self.question_text[:60]}"


class Assessment(models.Model):

    STATUS_CHOICES = [
        ('started', 'Started'),
        ('completed', 'Completed'),
    ]

    student    = models.ForeignKey(
        'students.StudentProfile',
        on_delete=models.CASCADE,
        related_name='assessments'
    )
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default='started')

    total_score       = models.IntegerField(default=0)
    aptitude_score    = models.IntegerField(default=0)
    personality_score = models.IntegerField(default=0)
    interest_score    = models.IntegerField(default=0)

    time_taken     = models.IntegerField(null=True, blank=True)
    attempt_number = models.IntegerField(default=1)

    created_at   = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Assessment #{self.id} — {self.student} [{self.status}]"


class AssessmentAnswer(models.Model):

    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answers'
    )

    selected_answer = models.CharField(max_length=1, null=True, blank=True)
    is_correct      = models.BooleanField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['assessment', 'question']

    def __str__(self):
        return f"Answer — Assessment #{self.assessment_id} Q#{self.question_id}"


class AssessmentReport(models.Model):

    assessment = models.OneToOneField(
        Assessment,
        on_delete=models.CASCADE,
        related_name='report'
    )
    student = models.ForeignKey(
        'students.StudentProfile',
        on_delete=models.CASCADE,
        related_name='reports'
    )

    personality_type    = models.CharField(max_length=100, null=True, blank=True)
    interest_areas      = models.JSONField(default=list)
    recommended_careers = models.JSONField(default=list)
    strengths           = models.JSONField(default=list)
    weaknesses          = models.JSONField(default=list)

    report_text    = models.TextField(null=True, blank=True)
    report_pdf_url = models.CharField(max_length=500, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report — {self.student} [{self.personality_type}]"