from django.urls import path
from .views import (
    CreateOrderView,
    RazorpayWebhookView,
    VerifyPaymentView,
    PointHistoryView,
)

urlpatterns = [
    path("create-order/", CreateOrderView.as_view(), name="create-order"),
    path("webhook/", RazorpayWebhookView.as_view(), name="razorpay-webhook"),
    path("verify/", VerifyPaymentView.as_view(), name="verify-payment"),
    path("history/", PointHistoryView.as_view(), name="point-history"),
]
