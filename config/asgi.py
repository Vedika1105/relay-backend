import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

from django.core.asgi import get_asgi_application

# This must be called before any app imports to ensure Django is fully loaded
django_asgi_app = get_asgi_application()

from channels.routing              import ProtocolTypeRouter, URLRouter
from channels.security.websocket   import AllowedHostsOriginValidator
from django.conf                   import settings
from apps.messaging.routing        import websocket_urlpatterns
from apps.messaging.middleware     import JWTWebSocketMiddleware

websocket_application = JWTWebSocketMiddleware(
    URLRouter(websocket_urlpatterns)
)

if not settings.DEBUG:
    websocket_application = AllowedHostsOriginValidator(websocket_application)

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': websocket_application,
})