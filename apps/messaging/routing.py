from django.urls import re_path
from .consumers  import ChatConsumer

websocket_urlpatterns = [
    # ws://localhost:8000/ws/chat/<channel_id>/
    re_path(r'ws/chat/(?P<channel_id>\d+)/$', ChatConsumer.as_asgi()),
]