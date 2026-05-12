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

        # TRIGGER NOTIFICATION (New logic for WebSocket)
        try:
            import re
            from notifications.utils import send_notification
            match = re.match(r"room_S(\d+)_C(\d+)", self.room_id)
            if match:
                s_id = int(match.group(1))
                c_id = int(match.group(2))
                receiver_id = c_id if int(sender_id) == s_id else s_id
                
                print(f"--- DEBUG: ChatConsumer Notification ---")
                print(f"    Receiver: {receiver_id} | Sender: {sender_id}")
                
                # Send the notification (Sync call in Async consumer)
                from asgiref.sync import sync_to_async
                await sync_to_async(send_notification)(
                    user_id=receiver_id,
                    title=f"New message from {sender_name}",
                    message=message_text[:100],
                    data={"room_id": self.room_id, "type": "chat_message"}
                )
        except Exception as e:
            print(f"--- DEBUG: ChatConsumer Notification Failed: {e} ---")

    @database_sync_to_async
    def save_message(self, sender_id, sender_name, text):
        room, created = ChatRoom.objects.get_or_create(room_id=self.room_id)
        return Message.objects.create(
            room=room, sender_id=sender_id, sender_name=sender_name, text=text
        )
