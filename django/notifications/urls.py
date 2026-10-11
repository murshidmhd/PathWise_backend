from django.urls import path
from .views import (
    FCMTokenView, 
    NotificationListView, 
    MarkNotificationReadView, 
    MarkAllNotificationsReadView,
    DeleteNotificationView,
    SendNotificationView
)

urlpatterns = [
    path("register-fcm/", FCMTokenView.as_view(), name="register_fcm"),
    path("latest/", NotificationListView.as_view(), name="notification_list"),
    path("read/<int:pk>/", MarkNotificationReadView.as_view(), name="mark_read"),
    path("mark-all-read/", MarkAllNotificationsReadView.as_view(), name="mark_all_read"),
    path("delete/<int:pk>/", DeleteNotificationView.as_view(), name="delete_notification"),
    path("send/", SendNotificationView.as_view(), name="send_notification_internal"),
]
