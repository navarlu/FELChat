from .models import User, Conversation, Message, AnswerRating


def start_conversation(session_id: str, title: str = "") -> Conversation:
    user, _ = User.objects.get_or_create(session_id=session_id)
    return Conversation.objects.create(user=user, title=title)


def add_message(conversation: Conversation, sender: str, text: str) -> Message:
    return Message.objects.create(conversation=conversation, sender=sender, text=text)


def rate_answer(message_id: int, rating: int, comment: str = "") -> AnswerRating:
    message = Message.objects.get(id=message_id)
    if message.sender != "bot":
        raise ValueError("Only bot messages can be rated.")
    return AnswerRating.objects.create(message=message, rating=rating, comment=comment)
