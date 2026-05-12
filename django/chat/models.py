from django.db import models


class ChatRoom(models.Model):
    """
    Groups messages into a room.
    room_id format: room_S{student_id}_C{counselor_id}
    We store student_id and counselor_id as integers to allow direct
    querying without parsing the room_id string.
    """

    room_id = models.CharField(max_length=255, unique=True)
    student_id = models.IntegerField(null=True, blank=True, db_index=True)
    counselor_id = models.IntegerField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Room {self.room_id} (Student: {self.student_id}, Counselor: {self.counselor_id})"


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
