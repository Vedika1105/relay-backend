from django.urls import path
from .views      import VoiceTokenView

urlpatterns = [
    path('<int:channel_id>/token/', VoiceTokenView.as_view(), name='voice-token'),
]