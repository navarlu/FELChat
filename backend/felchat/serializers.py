from rest_framework import serializers
from .models import User, Conversation, Message, AnswerRating


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = '__all__'



class MessageSerializer(serializers.ModelSerializer):
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'text', 'timestamp', 'rating']

    def get_rating(self, obj):
        if hasattr(obj, 'rating') and obj.rating:
            if obj.rating.rating == 1:
                return 'up'
            elif obj.rating.rating == -1:
                return 'down'
        return None


class AnswerRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerRating
        fields = '__all__'
