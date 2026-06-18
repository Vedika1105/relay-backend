from apps.servers.models import ServerMember, ServerMemberRole
from .models              import ChannelPermission

def is_server_admin(user, server):
    """
    Returns True if user is Owner or Admin in the server.
    Used to check if user can create/update/delete channels.
    """
    return ServerMember.objects.filter(
        server=server,
        user=user,
        role__in=[ServerMemberRole.OWNER, ServerMemberRole.ADMIN]
    ).exists()


def is_server_member(user, server):
    """
    Returns True if user is any kind of member in the server.
    Used to check if user can view channels.
    """
    return ServerMember.objects.filter(
        server=server,
        user=user
    ).exists()


# ── NEW — Channel Read/Write Permission ───────────────────
def get_channel_permission(user, channel):
    """
    Returns (can_read, can_write) for this user in this channel.
    Owner/Admin always get full access — they manage the server,
    so overrides never apply to them. If no override row exists
    for the user's role, default to full access.
    """
    membership = ServerMember.objects.filter(
        server=channel.server, user=user
    ).first()

    if not membership:
        return False, False

    if membership.role in [ServerMemberRole.OWNER, ServerMemberRole.ADMIN]:
        return True, True

    override = ChannelPermission.objects.filter(
        channel=channel, role=membership.role
    ).first()

    if not override:
        return True, True

    return override.can_read, override.can_write