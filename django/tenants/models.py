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
