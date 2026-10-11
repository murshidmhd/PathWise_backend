from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import ChatRoom, Message
from .serializers import ChatRoomSerializer, MessageSerializer
from notifications.utils import send_notification
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
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
        try:
            room_id = room_id.strip("/")
            room = ChatRoom.objects.filter(room_id=room_id).first()
            if not room:
                return Response([], status=status.HTTP_200_OK)
            
            messages = room.messages.all()
            serializer = MessageSerializer(messages, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"DEBUG: Error in ChatMessageView GET: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, room_id):
        """
        POST /api/chat/rooms/{room_id}/messages/
        """
        try:
            room_id = room_id.strip("/")

            # Parse student and counselor IDs from room_id (e.g. room_S138_C139)
            match = re.match(r"room_S(\d+)_C(\d+)", room_id)
            s_id = int(match.group(1)) if match else None
            c_id = int(match.group(2)) if match else None

            room, created = ChatRoom.objects.get_or_create(
                room_id=room_id,
                defaults={"student_id": s_id, "counselor_id": c_id},
            )
            # Backfill fields if room already existed but had no IDs
            if not created and (room.student_id is None or room.counselor_id is None):
                room.student_id = s_id
                room.counselor_id = c_id
                room.save(update_fields=["student_id", "counselor_id"])

            data = request.data
            sender_id = data.get("sender_id", 0)
            sender_name = data.get("sender_name", "Unknown")
            text = data.get("message", "")

            print(f"DEBUG: POST Message for {room_id} from {sender_name} ({sender_id})")

            message = Message.objects.create(
                room=room,
                sender_id=sender_id,
                sender_name=sender_name,
                text=text,
            )

            # TRIGGER NOTIFICATION
            if s_id and c_id:
                receiver_id = c_id if int(sender_id) == s_id else s_id
                print(f"--- DEBUG: ChatMessageView ---")
                print(f"    Room: {room_id} | S: {s_id} | C: {c_id}")
                print(f"    Sender: {sender_id} | Receiver: {receiver_id}")

                try:
                    send_notification(
                        user_id=receiver_id,
                        title=f"New message from {sender_name}",
                        message=text[:100] + ("..." if len(text) > 100 else ""),
                        data={"room_id": room_id, "type": "chat_message"},
                    )
                except Exception as n_err:
                    print(f"DEBUG: Notification failed (non-critical): {n_err}")

            serializer = MessageSerializer(message)
            
            # BROADCAST TO WEBSOCKET
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"chat_{room_id}",
                {
                    "type": "chat_message",
                    "message": text,
                    "sender_id": sender_id,
                    "sender_initials": sender_name[:2].upper() if sender_name else "??",
                    "timestamp": str(message.timestamp),
                },
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(f"DEBUG: Error in ChatMessageView POST: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

