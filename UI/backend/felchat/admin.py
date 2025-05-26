from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import User, Conversation, Message, AnswerRating

admin.site.register(User)
admin.site.register(Conversation)
admin.site.register(Message)
admin.site.register(AnswerRating)
