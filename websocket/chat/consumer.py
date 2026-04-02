from channels.generic.websocket import AsyncWebsocketConsumer
import json


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group = f"chat_{self.room_id}"

        # join the group
        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()

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
        message = data["message"]

        # broadcast to everyone in the room group
        await self.channel_layer.group_send(
            self.room_group,
            {
                "type": "chat_message",
                "message": message,
                # "sender_id": self.scope["user"].id,
                "sender_id": data.get(
                    "sender_id", 0
                ),  # ← client sends sender_id for now
                "sender_initials": data.get("sender_initials", "??"),
                "timestamp": data.get("timestamp"),
            },
        )
