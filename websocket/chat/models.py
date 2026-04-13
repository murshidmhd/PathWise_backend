from django.db import models


class ChatRoom(models.Model):
    """
    Groups messages into a room.
    In PathWise, room_id often corresponds to a Counselor or a specific session.
    """

    room_id = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Room {self.room_id}"


class Message(models.Model):
    """
    Individual chat messages.
    We store sender_id as an integer to maintain compatibility with the
    main Django accounts.User without needing to import the model here.
    """

    room = models.ForeignKey(
        ChatRoom, on_delete=models.CASCADE, related_name="messages"
    )
    sender_id = models.IntegerField()
    sender_name = models.CharField(max_length=255, blank=True, null=True)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return f"Message from {self.sender_id} in {self.room.room_id}"
