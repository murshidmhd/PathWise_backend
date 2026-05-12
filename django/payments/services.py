from django.db import transaction
from .models import Wallet, PointTransaction


class PointService:
    @staticmethod
    @transaction.atomic
    def add_points(user, amount, transaction_type, description):
        """
        Safely adds points to a user's wallet and logs the transaction.
        """
        wallet, _ = Wallet.objects.select_for_update().get_or_create(user=user)
        wallet.balance += amount
        wallet.save()

        PointTransaction.objects.create(
            user=user,
            amount=amount,
            transaction_type=transaction_type,
            description=description,
        )

        # NOTIFY STUDENT
        try:
            from notifications.utils import send_notification
            title = "Credits Added! 💰" if transaction_type == "PURCHASE" else "Bonus Credits! 🎁"
            send_notification(
                user_id=user.id,
                title=title,
                message=f"Success! {amount} Career Credits have been added to your wallet. Total Balance: {wallet.balance}",
                notification_type="payment"
            )
        except Exception as e:
            print(f"DEBUG: Payment notification failed: {e}")

        return wallet.balance

    @staticmethod
    @transaction.atomic
    def spend_points(user, amount, description):
        """
        Safely deducts points from a user's wallet and logs the transaction.
        Returns (True, new_balance) if successful, (False, current_balance) if insufficient funds.
        """
        wallet, _ = Wallet.objects.select_for_update().get_or_create(user=user)

        if wallet.balance < amount:
            return False, wallet.balance

        wallet.balance -= amount
        wallet.save()

        PointTransaction.objects.create(
            user=user, amount=-amount, transaction_type="SPEND", description=description
        )

        # NOTIFY STUDENT
        try:
            from notifications.utils import send_notification
            send_notification(
                user_id=user.id,
                title="Credits Spent 💳",
                message=f"You have used {amount} credits. Remaining balance: {wallet.balance}",
                notification_type="payment"
            )
        except Exception as e:
            print(f"DEBUG: Spend notification failed: {e}")

        return True, wallet.balance
