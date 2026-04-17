from django.urls import re_path
from .consumer import ChatConsumer

websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<room_id>[\w-]+)/$", ChatConsumer.as_asgi()),
]

# the room_id in here say the