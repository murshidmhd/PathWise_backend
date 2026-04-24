import razorpay
import json
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse
from django.db import transaction


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_spectacular.utils import extend_schema

from .models import Wallet, PaymentTransaction, PointTransaction
from .services import PointService

# Initialize Razorpay Client
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


class CreateOrderView(APIView):
    @extend_schema(
        responses={201: None}, description="Create a new Razorpay Order for SkillPoints"
    )
    def post(self, request):
        user = request.user
        points_to_add = int(request.data.get("points", 1))

        # Pricing logic:
        # 10 SP = 350
        # 35 SP = 999
        # 100 SP = 2499
        if points_to_add >= 100:
            amount_rupees = 2499
        elif points_to_add >= 35:
            amount_rupees = 999
        else:
            amount_rupees = 350

        # Razorpay expects amount in PAISA (Rupees * 100)
        razorpay_order = client.order.create(
            {
                "amount": amount_rupees * 100,
                "currency": "INR",
                "payment_capture": "1",
            }
        )

        # Save order tracking
        PaymentTransaction.objects.create(
            user=user,
            razorpay_order_id=razorpay_order["id"],
            amount_paid=amount_rupees,
            credits_added=points_to_add,
            status="PENDING",
        )

        return Response(
            {
                "order_id": razorpay_order["id"],
                "amount": amount_rupees * 100,
                "currency": "INR",
                "key": settings.RAZORPAY_KEY_ID,
            },
            status=status.HTTP_201_CREATED,
        )


@method_decorator(csrf_exempt, name="dispatch")
class RazorpayWebhookView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(exclude=True)  # Hide from swagger as it's for Razorpay
    def post(self, request):
        payload = request.body
        # sig_header = request.META.get('HTTP_X_RAZORPAY_SIGNATURE')

        try:
            # signature verification is currently bypassed for testing
            data = json.loads(payload)

            if data["event"] == "order.paid":
                order_id = data["payload"]["order"]["entity"]["id"]
                payment_id = data["payload"]["payment"]["entity"]["id"]

                txn = PaymentTransaction.objects.get(razorpay_order_id=order_id)
                if txn.status != "SUCCESS":
                    txn.status = "SUCCESS"
                    txn.razorpay_payment_id = payment_id
                    txn.save()

                    # Atomic add via service
                    PointService.add_points(
                        user=txn.user,
                        amount=txn.credits_added,
                        transaction_type="PURCHASE",
                        description=f"Purchased SkillPoints via Razorpay (Order: {order_id})",
                    )

            return HttpResponse(status=200)
        except Exception as e:
            return HttpResponse(status=400)

class VerifyPaymentView(APIView):
    def post(self, request):
        data = request.data
        razorpay_order_id = data.get("razorpay_order_id")
        
        params_dict = {
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": data.get("razorpay_payment_id"),
            "razorpay_signature": data.get("razorpay_signature"),
        }

        try:
            # 1. Verify the signature
            client.utility.verify_payment_signature(params_dict)

            # 2. Use atomic transaction and select_for_update to prevent double-crediting
            with transaction.atomic():
                txn = PaymentTransaction.objects.select_for_update().get(
                    razorpay_order_id=razorpay_order_id
                )
                
                if txn.status != "SUCCESS":
                    txn.status = "SUCCESS"
                    txn.razorpay_payment_id = params_dict["razorpay_payment_id"]
                    txn.save()

                    # Credit the points
                    PointService.add_points(
                        user=txn.user,
                        amount=txn.credits_added,
                        transaction_type="PURCHASE",
                        description=f"Verified SkillPoints (Order: {razorpay_order_id})",
                    )
                    return Response({"status": "Payment Verified & Points Added"}, status=status.HTTP_200_OK)
                else:
                    return Response({"status": "Already Processed"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"status": "Payment Verification Failed"}, status=status.HTTP_400_BAD_REQUEST)

class PointHistoryView(APIView):
    def get(self, request):
        transactions = PointTransaction.objects.filter(user=request.user).order_by(
            "-created_at"
        )
        data = [
            {
                "id": t.id,
                "amount": t.amount,
                "type": t.transaction_type,
                "description": t.description,
                "date": t.created_at.strftime("%Y-%m-%d %H:%M"),
            }
            for t in transactions
        ]

        wallet, _ = Wallet.objects.get_or_create(user=request.user)

        return Response({"balance": wallet.balance, "transactions": data})
