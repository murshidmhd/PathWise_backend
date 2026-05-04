from django.urls import path
from .views import FCMTokenView, NotificationListView, MarkNotificationReadView, SendNotificationView

urlpatterns = [
    path("register-fcm/", FCMTokenView.as_view(), name="register_fcm"),
    path("latest/", NotificationListView.as_view(), name="notification_list"),
    path("read/<int:pk>/", MarkNotificationReadView.as_view(), name="mark_read"),
    path("send/", SendNotificationView.as_view(), name="send_notification_internal"),
]
