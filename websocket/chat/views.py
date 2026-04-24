from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import ChatRoom, Message
from .serializers import ChatRoomSerializer, MessageSerializer
from notifications.utils import send_notification
import re


class ChatRoomListView(APIView):
    def get(self, request):
        rooms = ChatRoom.objects.all()
        serializer = ChatRoomSerializer(rooms, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ChatRoomSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChatRoomDetailView(APIView):
    def get(self, request, room_id):
        try:
            room = ChatRoom.objects.get(room_id=room_id)
        except ChatRoom.DoesNotExist:
            return Response(
                {"error": "Room not found"}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = ChatRoomSerializer(room)
        return Response(serializer.data)


class ChatMessageView(APIView):
    def get(self, request, room_id):
        """
        GET /api/chat/rooms/{room_id}/messages/
        """
        room, created = ChatRoom.objects.get_or_create(room_id=room_id)
        messages = room.messages.all()
        serializer = MessageSerializer(messages, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Failed to fetch messages: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    def post(self, request, room_id):
        """
        POST /api/chat/rooms/{room_id}/messages/
        """
        room, created = ChatRoom.objects.get_or_create(room_id=room_id)
        data = request.data
        sender_id = data.get("sender_id", 0)
        sender_name = data.get("sender_name", "Unknown")
        text = data.get("message", "")

        message = Message.objects.create(
            room=room,
            sender_id=sender_id,
            sender_name=sender_name,
            text=text,
        )

        # TRIGGER NOTIFICATION
        # Parse receiver_id from room_id (e.g., room_S5_C6)
        match = re.match(r"room_S(\d+)_C(\d+)", room_id)
        if match:
            s_id, c_id = map(int, match.groups())
            receiver_id = c_id if int(sender_id) == s_id else s_id

            send_notification(
                user_id=receiver_id,
                title=f"New message from {sender_name}",
                message=text[:100] + ("..." if len(text) > 100 else ""),
                data={"room_id": room_id, "type": "chat_message"},
            )

        serializer = MessageSerializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
