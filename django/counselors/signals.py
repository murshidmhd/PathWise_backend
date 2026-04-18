from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import CounselorRequest
from payments.services import PointService


@receiver(pre_save, sender=CounselorRequest)
def refund_on_rejection(sender, instance, **kwargs):
    """
    Automated refund of 10 SkillPoints if a Counselor Request is rejected.
    """
    if not instance.pk:
        return  # New request, nothing to refund yet

    try:
        old_instance = CounselorRequest.objects.get(pk=instance.pk)
    except CounselorRequest.DoesNotExist:
        return

    # Check for status transition from pending -> rejected
    if old_instance.status == "pending" and instance.status == "rejected":
        PointService.add_points(
            user=instance.student.user,
            amount=10,
            transaction_type="REFUND",
            description=f"Refund: Request for Counselor {instance.counselor.user.email} was rejected.",
        )
