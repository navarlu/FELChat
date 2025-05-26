from django.db import models
import uuid
from django.db import models


class User(models.Model):
    session_id = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.session_id)


class Conversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="conversations")
    started_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Conversation {self.id} ({self.title or 'No title'})"


class Message(models.Model):
    SENDER_CHOICES = (
        ("user", "User"),
        ("bot", "Bot"),
    )

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.capitalize()} @ {self.timestamp}: {self.text[:50]}"


class AnswerRating(models.Model):
    message = models.OneToOneField(Message, on_delete=models.CASCADE, related_name="rating")
    rating = models.IntegerField()  # e.g., 1 to 5 or -1/0/1
    comment = models.TextField(blank=True)
    rated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rating {self.rating} for message {self.message.id}"
