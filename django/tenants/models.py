from django.db import models
from django_tenants.models import TenantMixin, DomainMixin

class Organization(TenantMixin):
    name = models.CharField(max_length=200)        # "Vimal College"
    plan = models.CharField(max_length=50)         # "free" / "pro"
    created_at = models.DateTimeField(auto_now_add=True)

    # django-tenants requires this
    auto_create_schema = True

    def __str__(self):
        return self.name


class Domain(DomainMixin):
    pass


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


#note of mine 
# TenantMixin so basically this helps to get the schema of the tenant when a tenant login 
#this add the schema_name feild to the tenant model 
# and DomainMixin so basically this helps to get the domain of the tenant when a tenant login