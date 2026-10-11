from channels.generic.websocket import AsyncWebsocketConsumer
import json


class NotificationConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user_id = self.scope["url_route"]["kwargs"]["user_id"]
        self.user_group = f"user_{self.user_id}"

        await self.channel_layer.group_add(self.user_group, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.user_group, self.channel_name)

    async def notify(self, event):
        notification = event["notification"]
        print(f"--- DEBUG: NotificationConsumer received event for user {self.user_id}: {notification.get('title')} ---")
        await self.send(
            text_data=json.dumps(
                {
                    **notification,
                    "title": notification["title"],
                    "message": notification["message"],
                }
            )
        )
