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
        return True, wallet.balance
