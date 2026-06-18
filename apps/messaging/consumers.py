import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db                import database_sync_to_async
from django.utils                import timezone
from .models                    import Message, MAX_MESSAGE_LENGTH
from apps.chat.models           import Channel, ChannelType, ChannelPermission
from apps.servers.models        import ServerMember, ServerMemberRole
from apps.users.models          import UserStatus


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.channel_id = self.scope['url_route']['kwargs']['channel_id']
        self.room_group = f'chat_{self.channel_id}'
        self.user       = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        access = await self.check_access()
        if not access['can_read']:
            await self.close()
            return

        self.can_write = access['can_write']

        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()

        await self.set_online()
        await self.channel_layer.group_send(
            self.room_group,
            {
                'type'  : 'chat_message',
                'event' : 'presence',
                'user'  : self.user.username,
                'status': 'online',
            }
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group, self.channel_name)

        if hasattr(self, 'user') and self.user.is_authenticated:
            await self.set_offline()
            await self.channel_layer.group_send(
                self.room_group,
                {
                    'type'  : 'chat_message',
                    'event' : 'presence',
                    'user'  : self.user.username,
                    'status': 'offline',
                }
            )

    async def receive(self, text_data):
        data         = json.loads(text_data)
        message_type = data.get('type', 'send')
        content      = data.get('content', '').strip()
        message_id   = data.get('message_id')

        if message_type == 'send':
            await self.handle_send(content)
        elif message_type == 'edit':
            await self.handle_edit(message_id, content)
        elif message_type == 'delete':
            await self.handle_delete(message_id)

    async def handle_send(self, content):
        if not content:
            return

        if not self.can_write:
            await self.send(text_data=json.dumps({
                'error': 'You do not have write access to this channel.'
            }))
            return

        # ── NEW — enforce max message length ──
        if len(content) > MAX_MESSAGE_LENGTH:
            await self.send(text_data=json.dumps({
                'error': f'Messages must be {MAX_MESSAGE_LENGTH} characters or fewer.'
            }))
            return

        message = await self.save_message(content)
        await self.channel_layer.group_send(
            self.room_group,
            {
                'type'      : 'chat_message',
                'event'     : 'send',
                'message_id': message.id,
                'content'   : message.content,
                'sender'    : self.user.username,
                'created_at': str(message.created_at),
            }
        )

    async def handle_edit(self, message_id, content):
        if not content or not message_id:
            return

        if not self.can_write:
            await self.send(text_data=json.dumps({
                'error': 'You do not have write access to this channel.'
            }))
            return

        # ── NEW — enforce max message length ──
        if len(content) > MAX_MESSAGE_LENGTH:
            await self.send(text_data=json.dumps({
                'error': f'Messages must be {MAX_MESSAGE_LENGTH} characters or fewer.'
            }))
            return

        edited = await self.edit_message(message_id, content)
        if not edited:
            await self.send(text_data=json.dumps({
                'error': 'Cannot edit this message.'
            }))
            return
        await self.channel_layer.group_send(
            self.room_group,
            {
                'type'      : 'chat_message',
                'event'     : 'edit',
                'message_id': message_id,
                'content'   : content,
                'sender'    : self.user.username,
            }
        )

    async def handle_delete(self, message_id):
        if not message_id:
            return
        deleted = await self.delete_message(message_id)
        if not deleted:
            await self.send(text_data=json.dumps({
                'error': 'Cannot delete this message.'
            }))
            return
        await self.channel_layer.group_send(
            self.room_group,
            {
                'type'      : 'chat_message',
                'event'     : 'delete',
                'message_id': message_id,
                'sender'    : self.user.username,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def check_access(self):
        try:
            channel = Channel.objects.get(id=self.channel_id)
        except Channel.DoesNotExist:
            return {'can_read': False, 'can_write': False}

        if channel.channel_type != ChannelType.TEXT:
            return {'can_read': False, 'can_write': False}

        membership = ServerMember.objects.filter(
            server=channel.server,
            user=self.user
        ).first()

        if not membership:
            return {'can_read': False, 'can_write': False}

        if channel.is_private and membership.role not in [
            ServerMemberRole.OWNER, ServerMemberRole.ADMIN
        ]:
            return {'can_read': False, 'can_write': False}

        if membership.role in [ServerMemberRole.OWNER, ServerMemberRole.ADMIN]:
            return {'can_read': True, 'can_write': True}

        override = ChannelPermission.objects.filter(
            channel=channel, role=membership.role
        ).first()

        if not override:
            return {'can_read': True, 'can_write': True}

        return {'can_read': override.can_read, 'can_write': override.can_write}

    @database_sync_to_async
    def save_message(self, content):
        return Message.objects.create(
            channel_id=self.channel_id,
            sender=self.user,
            content=content
        )

    @database_sync_to_async
    def edit_message(self, message_id, content):
        try:
            message           = Message.objects.get(id=message_id, sender=self.user)
            message.content   = content
            message.is_edited = True
            message.save()
            return True
        except Message.DoesNotExist:
            return False

    @database_sync_to_async
    def delete_message(self, message_id):
        try:
            message = Message.objects.get(id=message_id)
            if message.sender == self.user:
                message.delete()
                return True
            channel  = Channel.objects.get(id=self.channel_id)
            is_admin = ServerMember.objects.filter(
                server=channel.server,
                user=self.user,
                role__in=[
                    ServerMemberRole.OWNER,
                    ServerMemberRole.ADMIN,
                    ServerMemberRole.MODERATOR
                ]
            ).exists()
            if is_admin:
                message.delete()
                return True
            return False
        except Message.DoesNotExist:
            return False

    @database_sync_to_async
    def set_online(self):
        self.user.status    = UserStatus.ONLINE
        self.user.last_seen = timezone.now()
        self.user.save()

    @database_sync_to_async
    def set_offline(self):
        self.user.status    = UserStatus.OFFLINE
        self.user.last_seen = timezone.now()
        self.user.save()