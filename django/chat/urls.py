from django.urls import path
from .views import ChatRoomListView, ChatRoomDetailView, ChatMessageView

urlpatterns = [
    path("rooms/", ChatRoomListView.as_view(), name="chat_room_list"),
    path("rooms/<str:room_id>/", ChatRoomDetailView.as_view(), name="chat_room_detail"),
    path(
        "rooms/<str:room_id>/messages/", ChatMessageView.as_view(), name="chat_messages"
    ),
]
