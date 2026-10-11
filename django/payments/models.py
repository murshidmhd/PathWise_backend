from django.db import models
from django.conf import settings


class Wallet(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wallet"
    )
    balance = models.IntegerField(default=0)  # Branded as SkillPoints in UI
    is_welcome_gift_claimed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.balance} SkillPoints"


class PointTransaction(models.Model):
    """
    Comprehensive ledger for all SkillPoint activity.
    """

    TRANSACTION_TYPES = [
        ("PURCHASE", "Purchase"),
        ("SPEND", "Spend"),
        ("GIFT", "Gift"),
        ("REFUND", "Refund"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="point_transactions",
    )
    amount = models.IntegerField()  # Positive for additions, negative for deductions
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} | {self.transaction_type} | {self.amount}"


class PaymentTransaction(models.Model):
    """
    Razorpay-specific transaction tracking.
    """

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    razorpay_order_id = models.CharField(max_length=100, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)  # Actual Rupees
    credits_added = models.IntegerField()  # Credits earned
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.razorpay_order_id} - {self.status}"
