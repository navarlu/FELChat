import random

from django.contrib.sites import requests
from django.forms import model_to_dict
from django.shortcuts import render
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import User, Conversation, Message, AnswerRating
from .serializers import UserSerializer, ConversationSerializer, MessageSerializer, AnswerRatingSerializer

import requests


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

    def get_queryset(self):
        conversation_id = self.request.query_params.get("conversation")
        if conversation_id:
            return Message.objects.filter(conversation_id=conversation_id).order_by("timestamp")
        return Message.objects.none()

    def perform_create(self, serializer):
        message = serializer.save()

        print("\nmessage\n", message)
        if message.sender == "user":

            try:

                messages = Message.objects.filter(conversation_id=message.conversation_id).order_by("timestamp")
                print("messages ", messages)

                serialized_messages = MessageSerializer(messages, many=True).data

                response = requests.post(
                    "http://host.docker.internal:5000/query",
                    json=serialized_messages
                )


                reply_text = response.json().get("answer", "Sorry, I didn't understand that.")
                print("reply_text", reply_text)
            except Exception as e:
                reply_text = f"(bot error: {str(e)})"
                print("bot error reply_text", reply_text)

            Message.objects.create(
                conversation=message.conversation,
                sender="bot",
                text=reply_text,
                timestamp=timezone.now()
            )


class AnswerRatingViewSet(viewsets.ModelViewSet):
    queryset = AnswerRating.objects.all()
    serializer_class = AnswerRatingSerializer

    def create(self, request, *args, **kwargs):
        message = request.data.get("message")
        value = request.data.get("value")
        comment = request.data.get("comment", "")

        rating, created = AnswerRating.objects.update_or_create(
            message_id=message,
            defaults={"rating": value, "comment": comment},
        )

        serializer = self.get_serializer(rating)
        return Response(serializer.data, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)


@api_view(['GET'])
def conversation_messages(request, conversation_id):
    try:
        conversation = Conversation.objects.get(pk=conversation_id)
    except Conversation.DoesNotExist:
        return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)

    messages = Message.objects.filter(conversation=conversation).order_by('timestamp')
    serializer = MessageSerializer(messages, many=True)
    return Response(serializer.data)

