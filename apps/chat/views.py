from rest_framework             import status
from rest_framework.response    import Response
from rest_framework.views       import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts           import get_object_or_404
from apps.servers.models        import Server, ServerMemberRole
from .models                    import Channel, ChannelPermission
from .serializers               import ChannelSerializer, CreateChannelSerializer, ChannelPermissionSerializer
from .permissions               import is_server_admin, is_server_member, get_channel_permission


class ChannelListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, server_id):
        server = get_object_or_404(Server, id=server_id)

        # check user is member of this server
        if not is_server_member(request.user, server):
            return Response(
                {'error': 'You are not a member of this server.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # if user is admin/owner → show all channels including private
        # if user is member → show only public channels
        if is_server_admin(request.user, server):
            channels = Channel.objects.filter(server=server)
        else:
            channels = Channel.objects.filter(server=server, is_private=False)

        return Response(
            ChannelSerializer(channels, many=True).data,
            status=status.HTTP_200_OK
        )

    def post(self, request, server_id):
        server = get_object_or_404(Server, id=server_id)

        # only admin/owner can create channels
        if not is_server_admin(request.user, server):
            return Response(
                {'error': 'Only admins and owners can create channels.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = CreateChannelSerializer(data=request.data)

        if serializer.is_valid():
            # check duplicate channel name in this server
            if Channel.objects.filter(
                server=server,
                name=serializer.validated_data['name']
            ).exists():
                return Response(
                    {'error': 'Channel with this name already exists in this server.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            channel = serializer.save(
                server=server,
                created_by=request.user
            )
            return Response(
                ChannelSerializer(channel).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChannelDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_channel(self, server_id, channel_id):
        # reusable method to get channel
        server  = get_object_or_404(Server, id=server_id)
        channel = get_object_or_404(Channel, id=channel_id, server=server)
        return server, channel

    def get(self, request, server_id, channel_id):
        server, channel = self.get_channel(server_id, channel_id)

        if not is_server_member(request.user, server):
            return Response(
                {'error': 'You are not a member of this server.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # private channel → only admin/owner can view
        if channel.is_private and not is_server_admin(request.user, server):
            return Response(
                {'error': 'You do not have access to this channel.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # ── NEW — per-role read override check ──
        can_read, _ = get_channel_permission(request.user, channel)
        if not can_read:
            return Response(
                {'error': 'You do not have read access to this channel.'},
                status=status.HTTP_403_FORBIDDEN
            )

        return Response(
            ChannelSerializer(channel).data,
            status=status.HTTP_200_OK
        )

    def put(self, request, server_id, channel_id):
        server, channel = self.get_channel(server_id, channel_id)

        if not is_server_admin(request.user, server):
            return Response(
                {'error': 'Only admins and owners can update channels.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = CreateChannelSerializer(
            channel,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                ChannelSerializer(channel).data,
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, server_id, channel_id):
        server, channel = self.get_channel(server_id, channel_id)

        if not is_server_admin(request.user, server):
            return Response(
                {'error': 'Only admins and owners can delete channels.'},
                status=status.HTTP_403_FORBIDDEN
            )

        channel.delete()
        return Response(
            {'message': 'Channel deleted successfully.'},
            status=status.HTTP_200_OK
        )


# ── NEW — Channel Permission Overrides ──────────────────
class ChannelPermissionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, server_id, channel_id):
        server  = get_object_or_404(Server, id=server_id)
        channel = get_object_or_404(Channel, id=channel_id, server=server)

        if not is_server_admin(request.user, server):
            return Response(
                {'error': 'Only admins and owners can view permission overrides.'},
                status=status.HTTP_403_FORBIDDEN
            )

        overrides = ChannelPermission.objects.filter(channel=channel)
        return Response(
            ChannelPermissionSerializer(overrides, many=True).data,
            status=status.HTTP_200_OK
        )

    def put(self, request, server_id, channel_id):
        server  = get_object_or_404(Server, id=server_id)
        channel = get_object_or_404(Channel, id=channel_id, server=server)

        if not is_server_admin(request.user, server):
            return Response(
                {'error': 'Only admins and owners can set permission overrides.'},
                status=status.HTTP_403_FORBIDDEN
            )

        role = request.data.get('role')
        # overrides only ever apply to moderator/member —
        # owner/admin always bypass them by design
        valid_roles = [ServerMemberRole.MODERATOR, ServerMemberRole.MEMBER]

        if role not in valid_roles:
            return Response(
                {'error': 'Overrides can only be set for moderator or member roles.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        can_read  = request.data.get('can_read', True)
        can_write = request.data.get('can_write', True)

        override, created = ChannelPermission.objects.update_or_create(
            channel=channel,
            role=role,
            defaults={'can_read': can_read, 'can_write': can_write}
        )

        return Response(
            ChannelPermissionSerializer(override).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )