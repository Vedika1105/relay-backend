import os
from django.core.asgi              import get_asgi_application
from channels.routing              import ProtocolTypeRouter, URLRouter
from channels.security.websocket   import AllowedHostsOriginValidator
from django.conf                   import settings
from apps.messaging.routing        import websocket_urlpatterns
from apps.messaging.middleware     import JWTWebSocketMiddleware

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

django_asgi_app = get_asgi_application()

websocket_application = JWTWebSocketMiddleware(
    URLRouter(websocket_urlpatterns)
)

# Origin validation only matters against real browsers, which always send
# an Origin header automatically. Postman often sends no Origin header at
# all, which AllowedHostsOriginValidator treats as invalid and blocks — so
# we only enable this check when DEBUG is off, i.e. in production, where
# all traffic is real browsers hitting our actual deployed frontend.
if not settings.DEBUG:
    websocket_application = AllowedHostsOriginValidator(websocket_application)

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': websocket_application,
})