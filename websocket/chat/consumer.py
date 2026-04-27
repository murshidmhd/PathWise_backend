from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, Message
import json


class ChatConsumer(AsyncWebsocketConsumer):
    # async def connect(self):
    #     self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
    #     # we crete the
    #     self.room_group = f"chat_{self.room_id}"

    #     # join the group
    #     await self.channel_layer.group_add(self.room_group, self.channel_name)
    #     await self.accept()

    async def connect(self):
        print("--- DEBUG: Connection attempt started ---")
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group = f"chat_{self.room_id}"

        # Join the room group
        await self.channel_layer.group_add(self.room_group, self.channel_name)

        # Accept the connection
        await self.accept()
        print(f"--- DEBUG: Connection ACCEPTED for room: {self.room_id} ---")


    async def disconnect(self, close_code):
        # leave the group
        await self.channel_layer.group_discard(self.room_group, self.channel_name)

    async def chat_message(self, event):
        # receives from Redis, sends to client
        await self.send(
            text_data=json.dumps(
                {
                    "message": event["message"],
                    "sender_id": event["sender_id"],
                    "sender_initials": event.get("sender_initials", "??"),
                    "timestamp": event.get("timestamp"),
                }
            )
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_text = data["message"]
        sender_id = data.get("sender_id", 0)
        sender_name = data.get("sender_name", "Unknown")

        # Save to database
        await self.save_message(sender_id, sender_name, message_text)

        # broadcast to everyone in the room group
        await self.channel_layer.group_send(
            self.room_group,
            {
                "type": "chat_message",
                "message": message_text,
                "sender_id": sender_id,
                "sender_initials": data.get("sender_initials", "??"),
                "timestamp": data.get("timestamp"),
            },
        )

    @database_sync_to_async
    def save_message(self, sender_id, sender_name, text):
        room, created = ChatRoom.objects.get_or_create(room_id=self.room_id)
        return Message.objects.create(
            room=room, sender_id=sender_id, sender_name=sender_name, text=text
        )
