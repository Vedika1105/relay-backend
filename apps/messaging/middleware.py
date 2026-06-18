from channels.middleware         import BaseMiddleware
from channels.db                 import database_sync_to_async
from django.contrib.auth.models  import AnonymousUser
from rest_framework_simplejwt.tokens     import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from urllib.parse                import parse_qs
from apps.users.models           import User


@database_sync_to_async
def get_user_from_token(token_string):
    try:
        # decode JWT token → get user_id
        token   = AccessToken(token_string)
        user_id = token['user_id']
        return User.objects.get(id=user_id)
    except (InvalidToken, TokenError, User.DoesNotExist):
        return AnonymousUser()


class JWTWebSocketMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        # get token from URL query parameter
        # ws://localhost:8000/ws/chat/1/?token=eyJ...
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        token_list   = query_params.get('token', [None])
        token        = token_list[0] if token_list else None

        if token:
            scope['user'] = await get_user_from_token(token)
        else:
            scope['user'] = AnonymousUser()

        return await super().__call__(scope, receive, send)