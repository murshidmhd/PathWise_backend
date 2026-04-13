from django.urls import path
from .views import FCMTokenView

urlpatterns = [
    path("register-fcm/", FCMTokenView.as_view(), name="register_fcm"),
]
