"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

# from django.contrib import admin
# from django.urls import path
#
# urlpatterns = [
#     path("admin/", admin.site.urls),
# ]
#

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from felchat.views import (
    UserViewSet, ConversationViewSet, MessageViewSet, AnswerRatingViewSet, conversation_messages
)

# router = DefaultRouter()
# router.register(r'users', UserViewSet)
# router.register(r'conversations', ConversationViewSet)
# router.register(r'messages', MessageViewSet)
# router.register(r'ratings', AnswerRatingViewSet)
#
# urlpatterns = [
#     path('api/', include(router.urls)),
# ]

router = DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'ratings', AnswerRatingViewSet, basename='rating')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('conversations/<int:conversation_id>/messages/', conversation_messages),
]


