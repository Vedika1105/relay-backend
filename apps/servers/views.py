from rest_framework              import status
from rest_framework.response     import Response
from rest_framework.views        import APIView
from rest_framework.permissions  import IsAuthenticated
from django.shortcuts            import get_object_or_404
from .models                     import Server, ServerMember, ServerMemberRole, ServerBan
from .serializers                import (ServerSerializer, CreateServerSerializer,
                                         UpdateServerSerializer, ServerMemberSerializer,
                                         ServerBanSerializer)


class CreateServerView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateServerSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            server = serializer.save()
            return Response(
                ServerSerializer(server).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MyServersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # get all servers where this user is a member
        # values_list → efficient, only fetches server_id not full objects
        server_ids = ServerMember.objects.filter(
            user=request.user
        ).values_list('server_id', flat=True)

        servers = Server.objects.filter(id__in=server_ids)
        return Response(
            ServerSerializer(servers, many=True).data,
            status=status.HTTP_200_OK
        )


class ServerDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, server_id):
        # get_object_or_404 → returns 404 if server not found
        server = get_object_or_404(Server, id=server_id)

        # check requesting user is a member of this server
        is_member = ServerMember.objects.filter(
            server=server,
            user=request.user
        ).exists()

        if not is_member:
            return Response(
                {'error': 'You are not a member of this server.'},
                status=status.HTTP_403_FORBIDDEN
            )

        return Response(
            ServerSerializer(server).data,
            status=status.HTTP_200_OK
        )

    def put(self, request, server_id):
        server = get_object_or_404(Server, id=server_id)

        # only owner can update server
        if server.owner != request.user:
            return Response(
                {'error': 'Only the server owner can update server details.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = UpdateServerSerializer(server, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                ServerSerializer(server).data,
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, server_id):
        server = get_object_or_404(Server, id=server_id)

        # only owner can delete server
        if server.owner != request.user:
            return Response(
                {'error': 'Only the server owner can delete the server.'},
                status=status.HTTP_403_FORBIDDEN
            )

        server.delete()
        return Response(
            {'message': 'Server deleted successfully.'},
            status=status.HTTP_200_OK
        )


class JoinServerView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        invite_code = request.data.get('invite_code')

        if not invite_code:
            return Response(
                {'error': 'Invite code is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # find server with this invite code
        server = get_object_or_404(Server, invite_code=invite_code)

        # ── NEW — block banned users from rejoining ──
        if ServerBan.objects.filter(server=server, user=request.user).exists():
            return Response(
                {'error': 'You are banned from this server.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # check if already a member
        already_member = ServerMember.objects.filter(
            server=server,
            user=request.user
        ).exists()

        if already_member:
            return Response(
                {'error': 'You are already a member of this server.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # add user as member
        ServerMember.objects.create(
            server=server,
            user=request.user,
            role=ServerMemberRole.MEMBER
        )

        return Response(
            ServerSerializer(server).data,
            status=status.HTTP_200_OK
        )


class LeaveServerView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, server_id):
        server = get_object_or_404(Server, id=server_id)

        # owner cannot leave their own server
        if server.owner == request.user:
            return Response(
                {'error': 'Owner cannot leave the server. Transfer ownership or delete the server.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        membership = ServerMember.objects.filter(
            server=server,
            user=request.user
        ).first()

        if not membership:
            return Response(
                {'error': 'You are not a member of this server.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        membership.delete()
        return Response(
            {'message': 'Left server successfully.'},
            status=status.HTTP_200_OK
        )


class ServerMembersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, server_id):
        server = get_object_or_404(Server, id=server_id)

        # only members can see member list
        is_member = ServerMember.objects.filter(
            server=server,
            user=request.user
        ).exists()

        if not is_member:
            return Response(
                {'error': 'You are not a member of this server.'},
                status=status.HTTP_403_FORBIDDEN
            )

        members = ServerMember.objects.filter(server=server)
        return Response(
            ServerMemberSerializer(members, many=True).data,
            status=status.HTTP_200_OK
        )


# ── NEW — Role Assignment ───────────────────────────────
class UpdateMemberRoleView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, server_id, user_id):
        server = get_object_or_404(Server, id=server_id)

        requester_membership = ServerMember.objects.filter(
            server=server,
            user=request.user
        ).first()

        if not requester_membership or requester_membership.role not in [
            ServerMemberRole.OWNER, ServerMemberRole.ADMIN
        ]:
            return Response(
                {'error': 'Only the owner or an admin can assign roles.'},
                status=status.HTTP_403_FORBIDDEN
            )

        target_membership = ServerMember.objects.filter(
            server=server,
            user_id=user_id
        ).first()

        if not target_membership:
            return Response(
                {'error': 'This user is not a member of the server.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if target_membership.role == ServerMemberRole.OWNER:
            return Response(
                {'error': 'Owner role cannot be changed here. Use transfer ownership instead.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_role = request.data.get('role')
        valid_roles = [ServerMemberRole.ADMIN, ServerMemberRole.MODERATOR, ServerMemberRole.MEMBER]

        if new_role not in valid_roles:
            return Response(
                {'error': 'Role must be one of: admin, moderator, member.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if requester_membership.role == ServerMemberRole.ADMIN:
            if new_role == ServerMemberRole.ADMIN:
                return Response(
                    {'error': 'Only the owner can promote a member to admin.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            if target_membership.role == ServerMemberRole.ADMIN:
                return Response(
                    {'error': "Only the owner can change another admin's role."},
                    status=status.HTTP_403_FORBIDDEN
                )

        target_membership.role = new_role
        target_membership.save()

        return Response(
            ServerMemberSerializer(target_membership).data,
            status=status.HTTP_200_OK
        )


# ── NEW — Kick Member ───────────────────────────────────
class KickMemberView(APIView):
    permission_classes = [IsAuthenticated]

    ROLE_RANK = {
        ServerMemberRole.OWNER: 4,
        ServerMemberRole.ADMIN: 3,
        ServerMemberRole.MODERATOR: 2,
        ServerMemberRole.MEMBER: 1,
    }

    def post(self, request, server_id, user_id):
        server = get_object_or_404(Server, id=server_id)

        requester_membership = ServerMember.objects.filter(
            server=server, user=request.user
        ).first()

        if not requester_membership or requester_membership.role not in [
            ServerMemberRole.OWNER, ServerMemberRole.ADMIN, ServerMemberRole.MODERATOR
        ]:
            return Response(
                {'error': 'Only the owner, admins, or moderators can kick members.'},
                status=status.HTTP_403_FORBIDDEN
            )

        target_membership = ServerMember.objects.filter(
            server=server, user_id=user_id
        ).first()

        if not target_membership:
            return Response(
                {'error': 'This user is not a member of the server.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if target_membership.role == ServerMemberRole.OWNER:
            return Response(
                {'error': 'The owner cannot be kicked.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if self.ROLE_RANK[requester_membership.role] <= self.ROLE_RANK[target_membership.role]:
            return Response(
                {'error': 'You cannot kick a member with an equal or higher role.'},
                status=status.HTTP_403_FORBIDDEN
            )

        target_membership.delete()
        return Response(
            {'message': 'Member kicked successfully.'},
            status=status.HTTP_200_OK
        )


# ── NEW — Transfer Ownership ────────────────────────────
class TransferOwnershipView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, server_id):
        server = get_object_or_404(Server, id=server_id)

        if server.owner != request.user:
            return Response(
                {'error': 'Only the current owner can transfer ownership.'},
                status=status.HTTP_403_FORBIDDEN
            )

        new_owner_id = request.data.get('new_owner_id')
        if not new_owner_id:
            return Response(
                {'error': 'new_owner_id is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_owner_membership = ServerMember.objects.filter(
            server=server, user_id=new_owner_id
        ).first()

        if not new_owner_membership:
            return Response(
                {'error': 'The new owner must already be a member of this server.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        old_owner_membership = ServerMember.objects.filter(
            server=server, user=request.user
        ).first()

        server.owner = new_owner_membership.user
        server.save()

        new_owner_membership.role = ServerMemberRole.OWNER
        new_owner_membership.save()

        old_owner_membership.role = ServerMemberRole.ADMIN
        old_owner_membership.save()

        return Response(
            ServerSerializer(server).data,
            status=status.HTTP_200_OK
        )


# ── NEW — Ban Member ────────────────────────────────────
class BanMemberView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, server_id, user_id):
        server = get_object_or_404(Server, id=server_id)

        requester_membership = ServerMember.objects.filter(
            server=server, user=request.user
        ).first()

        # only Owner or Admin can ban — Moderators can kick but not ban
        if not requester_membership or requester_membership.role not in [
            ServerMemberRole.OWNER, ServerMemberRole.ADMIN
        ]:
            return Response(
                {'error': 'Only the owner or an admin can ban members.'},
                status=status.HTTP_403_FORBIDDEN
            )

        target_membership = ServerMember.objects.filter(
            server=server, user_id=user_id
        ).first()

        if not target_membership:
            return Response(
                {'error': 'This user is not a member of the server.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if target_membership.role == ServerMemberRole.OWNER:
            return Response(
                {'error': 'The owner cannot be banned.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if requester_membership.role == ServerMemberRole.ADMIN and target_membership.role == ServerMemberRole.ADMIN:
            return Response(
                {'error': 'Only the owner can ban another admin.'},
                status=status.HTTP_403_FORBIDDEN
            )

        ServerBan.objects.get_or_create(
            server=server,
            user_id=user_id,
            defaults={
                'banned_by': request.user,
                'reason': request.data.get('reason')
            }
        )

        target_membership.delete()

        return Response(
            {'message': 'Member banned successfully.'},
            status=status.HTTP_200_OK
        )


# ── NEW — Unban Member ──────────────────────────────────
class UnbanMemberView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, server_id, user_id):
        server = get_object_or_404(Server, id=server_id)

        requester_membership = ServerMember.objects.filter(
            server=server, user=request.user
        ).first()

        if not requester_membership or requester_membership.role not in [
            ServerMemberRole.OWNER, ServerMemberRole.ADMIN
        ]:
            return Response(
                {'error': 'Only the owner or an admin can unban members.'},
                status=status.HTTP_403_FORBIDDEN
            )

        ban = ServerBan.objects.filter(server=server, user_id=user_id).first()
        if not ban:
            return Response(
                {'error': 'This user is not banned.'},
                status=status.HTTP_404_NOT_FOUND
            )

        ban.delete()
        return Response(
            {'message': 'Member unbanned successfully.'},
            status=status.HTTP_200_OK
        )


# ── NEW — List Bans ─────────────────────────────────────
class ServerBansView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, server_id):
        server = get_object_or_404(Server, id=server_id)

        requester_membership = ServerMember.objects.filter(
            server=server, user=request.user
        ).first()

        if not requester_membership or requester_membership.role not in [
            ServerMemberRole.OWNER, ServerMemberRole.ADMIN
        ]:
            return Response(
                {'error': 'Only the owner or an admin can view the ban list.'},
                status=status.HTTP_403_FORBIDDEN
            )

        bans = ServerBan.objects.filter(server=server)
        return Response(
            ServerBanSerializer(bans, many=True).data,
            status=status.HTTP_200_OK
        )