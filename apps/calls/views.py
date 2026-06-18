import time
from rest_framework             import status
from rest_framework.response    import Response
from rest_framework.views       import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts           import get_object_or_404
from django.conf                import settings
from agora_token_builder        import RtcTokenBuilder
from apps.chat.models           import Channel, ChannelType
from apps.chat.permissions      import is_server_admin, is_server_member, get_channel_permission


class VoiceTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, channel_id):
        channel = get_object_or_404(Channel, id=channel_id)
        server  = channel.server

        if not is_server_member(request.user, server):
            return Response(
                {'error': 'You are not a member of this server.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # only voice/video channels can issue call tokens
        if channel.channel_type not in [ChannelType.VOICE, ChannelType.VIDEO]:
            return Response(
                {'error': 'This channel does not support voice/video.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # private channel → only admin/owner can join
        if channel.is_private and not is_server_admin(request.user, server):
            return Response(
                {'error': 'You do not have access to this channel.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # per-role read override check — same helper used for text channels
        can_read, _ = get_channel_permission(request.user, channel)
        if not can_read:
            return Response(
                {'error': 'You do not have read access to this channel.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # one Agora room per Channel row — unique, deterministic name
        agora_channel_name = f'channel_{channel.id}'

        # token valid for 1 hour — same lifetime reasoning as our JWT access token
        expire_seconds      = 3600
        current_ts          = int(time.time())
        privilege_expire_ts = current_ts + expire_seconds
        role                = 1  # Publisher — can speak/share video AND hear/see others

        token = RtcTokenBuilder.buildTokenWithUid(
            settings.AGORA_APP_ID,
            settings.AGORA_APP_CERTIFICATE,
            agora_channel_name,
            request.user.id,
            role,
            privilege_expire_ts
        )

        return Response({
            'app_id'      : settings.AGORA_APP_ID,
            'token'       : token,
            'channel_name': agora_channel_name,
            'uid'         : request.user.id,
            'expires_in'  : expire_seconds
        }, status=status.HTTP_200_OK)