import uuid
from django.db import models
from django.conf import settings

class SimulationScenario(models.Model):
    SCENARIO_TYPES = [
        ('STAKEHOLDER', 'Stakeholder Meeting'),
        ('DEBATE', 'Competitive Debate'),
        ('CRISIS', 'Crisis Management'),
        ('PAIR_PROGRAMMING', 'Pair Programming'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    scenario_type = models.CharField(max_length=50, choices=SCENARIO_TYPES)
    agent_configs = models.JSONField(help_text="List of agents with their names, descriptions, and personas")
    initial_prompt = models.TextField(help_text="The opening prompt to start the scenario")
    rules = models.JSONField(help_text="Objectives, time limits, evaluation rubrics")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.get_scenario_type_display()})"

class SimulationSession(models.Model):
    STATUS_CHOICES = [
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('PAUSED', 'Paused'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='simulation_sessions')
    scenario = models.ForeignKey(SimulationScenario, on_delete=models.CASCADE, related_name='sessions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IN_PROGRESS')
    
    stress_level = models.IntegerField(default=50, help_text="Dynamic sentiment metric 0-100")
    confidence_level = models.IntegerField(default=50, help_text="Dynamic sentiment metric 0-100")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.email} - {self.scenario.title} ({self.status})"

class SimulationMessage(models.Model):
    ROLE_CHOICES = [
        ('USER', 'User'),
        ('AGENT', 'Agent'),
        ('COACH', 'Coach'),
    ]

    session = models.ForeignKey(SimulationSession, on_delete=models.CASCADE, related_name='messages')
    sender_role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    sender_name = models.CharField(max_length=255)
    text = models.TextField()
    sentiment_score = models.FloatField(null=True, blank=True, help_text="-1.0 to 1.0")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"[{self.timestamp}] {self.sender_name}: {self.text[:50]}"

class PostActionReport(models.Model):
    session = models.OneToOneField(SimulationSession, on_delete=models.CASCADE, related_name='report')
    score_negotiation = models.IntegerField(default=0)
    score_professionalism = models.IntegerField(default=0)
    score_clarity = models.IntegerField(default=0)
    score_overall = models.IntegerField(default=0)
    
    feedback_text = models.TextField()
    heatmap_data = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report for {self.session.id}"
