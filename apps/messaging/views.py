import os
from asgiref.sync               import async_to_sync
from channels.layers            import get_channel_layer
from rest_framework             import status
from rest_framework.response    import Response
from rest_framework.views       import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers     import MultiPartParser
from django.shortcuts           import get_object_or_404
from .models                    import Message
from .serializers               import MessageSerializer
from apps.chat.models           import Channel, ChannelType
from apps.chat.permissions      import get_channel_permission
from apps.servers.models        import ServerMember, ServerMemberRole
from .models import Message, MAX_MESSAGE_LENGTH

IMAGE_EXTENSIONS    = {'.jpg', '.jpeg', '.png'}
ALLOWED_EXTENSIONS  = IMAGE_EXTENSIONS | {'.pdf', '.txt', '.doc', '.docx', '.zip'}
MAX_ATTACHMENT_SIZE = 5 * 1024 * 1024  # 5MB flat limit for everything allowed


class MessageHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, channel_id):
        channel = get_object_or_404(Channel, id=channel_id)

        is_member = ServerMember.objects.filter(
            server=channel.server,
            user=request.user
        ).exists()

        if not is_member:
            return Response(
                {'error': 'You are not a member of this server.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # ── NEW — per-role read override check ──
        can_read, _ = get_channel_permission(request.user, channel)
        if not can_read:
            return Response(
                {'error': 'You do not have read access to this channel.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # ── NEW — cursor-based pagination ──
        # before → id of the oldest message the client already has
        # not provided → first load → return the latest 50
        before_id = request.query_params.get('before')

        messages = Message.objects.filter(channel=channel)

        if before_id:
            messages = messages.filter(id__lt=before_id)

        # newest first for slicing (grabs the most recent 50),
        # then reverse so the response stays oldest→newest for rendering
        messages = list(messages.order_by('-id')[:50])
        messages.reverse()

        next_cursor = messages[0].id if messages else None

        return Response({
            'results'    : MessageSerializer(messages, many=True).data,
            'next_cursor': next_cursor,
            'has_more'   : len(messages) == 50
        }, status=status.HTTP_200_OK)


class MessageActionView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, message_id):
        message = get_object_or_404(Message, id=message_id)

        if message.sender != request.user:
            return Response(
                {'error': 'You can only edit your own messages.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # ── NEW — editing is writing, same channel permission applies ──
        _, can_write = get_channel_permission(request.user, message.channel)
        if not can_write:
            return Response(
                {'error': 'You do not have write access to this channel.'},
                status=status.HTTP_403_FORBIDDEN
            )

        content = request.data.get('content', '').strip()

        if len(content) > MAX_MESSAGE_LENGTH:
            return Response(
                {'error': f'Messages must be {MAX_MESSAGE_LENGTH} characters or fewer.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not content:
            return Response(
                {'error': 'Message content cannot be empty.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        message.content   = content
        message.is_edited = True
        message.save()

        return Response(
            MessageSerializer(message).data,
            status=status.HTTP_200_OK
        )

    def delete(self, request, message_id):
        message = get_object_or_404(Message, id=message_id)
        channel = message.channel

        if message.sender == request.user:
            message.delete()
            return Response(
                {'message': 'Message deleted successfully.'},
                status=status.HTTP_200_OK
            )

        is_admin = ServerMember.objects.filter(
            server=channel.server,
            user=request.user,
            role__in=[
                ServerMemberRole.OWNER,
                ServerMemberRole.ADMIN,
                ServerMemberRole.MODERATOR
            ]
        ).exists()

        if is_admin:
            message.delete()
            return Response(
                {'message': 'Message deleted successfully.'},
                status=status.HTTP_200_OK
            )

        return Response(
            {'error': 'You do not have permission to delete this message.'},
            status=status.HTTP_403_FORBIDDEN
        )


class MessageAttachmentUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes     = [MultiPartParser]

    def post(self, request, channel_id):
        channel = get_object_or_404(Channel, id=channel_id)

        if channel.channel_type != ChannelType.TEXT:
            return Response(
                {'error': 'Attachments can only be sent in text channels.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        is_member = ServerMember.objects.filter(server=channel.server, user=request.user).exists()
        if not is_member:
            return Response(
                {'error': 'You are not a member of this server.'},
                status=status.HTTP_403_FORBIDDEN
            )

        _, can_write = get_channel_permission(request.user, channel)
        if not can_write:
            return Response(
                {'error': 'You do not have write access to this channel.'},
                status=status.HTTP_403_FORBIDDEN
            )

        file    = request.FILES.get('attachment')
        content = request.data.get('content', '').strip()

        if not file and not content:
            return Response(
                {'error': 'Message must have text or an attachment.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(content) > MAX_MESSAGE_LENGTH:
            return Response(
                {'error': f'Messages must be {MAX_MESSAGE_LENGTH} characters or fewer.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if file:
            # Blocks the classic double-extension trick, e.g. "invoice.pdf.exe"
            if file.name.count('.') != 1:
                return Response(
                    {'error': 'Filename must have exactly one extension.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                return Response(
                    {'error': 'That file type is not allowed.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if file.size > MAX_ATTACHMENT_SIZE:
                return Response(
                    {'error': 'File must be smaller than 5MB.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        message = Message.objects.create(
            channel=channel,
            sender=request.user,
            content=content,
            attachment=file,
            attachment_name=file.name if file else None,
            attachment_size=file.size if file else None,
        )

        # Broadcasts through the exact same group and event shape the
        # consumer already uses for a typed message, so it appears live
        # for everyone — including the uploader's own connection —
        # without the frontend ever needing to add it from this response.
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'chat_{channel_id}',
            {
                'type'           : 'chat_message',
                'event'          : 'send',
                'message_id'     : message.id,
                'content'        : message.content,
                'sender'         : request.user.username,
                'created_at'     : str(message.created_at),
                'attachment_url' : message.attachment.url if message.attachment else None,
                'attachment_name': message.attachment_name,
                'attachment_size': message.attachment_size,
            }
        )

        return Response(
            {'success': True, 'message_id': message.id},
            status=status.HTTP_201_CREATED
        )