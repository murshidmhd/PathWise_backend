from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import Wallet
from .services import PointService


@receiver(user_logged_in)
def grant_welcome_gift(sender, request, user, **kwargs):
    """
    Grants 10 SkillPoints to a user upon their first login.
    """
    wallet, created = Wallet.objects.get_or_create(user=user)

    if not wallet.is_welcome_gift_claimed:
        PointService.add_points(
            user=user,
            amount=10,
            transaction_type="GIFT",
            description="Welcome Gift: 10 SkillPoints credited for joining PathWise!",
        )
        wallet.is_welcome_gift_claimed = True
        wallet.save()
