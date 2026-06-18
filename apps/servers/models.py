import uuid
from django.db   import models
from django.conf import settings


class Server(models.Model):
    name        = models.CharField(max_length=100)
    description = models.TextField(max_length=500, null=True, blank=True)
    icon        = models.ImageField(upload_to='server_icons/', null=True, blank=True)
    invite_code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False) # random unique code
    owner       = models.ForeignKey(
                    settings.AUTH_USER_MODEL,  # points to our custom User
                    on_delete=models.CASCADE,  # delete server if owner deleted
                    related_name='owned_servers'
                  )
    created_at  = models.DateTimeField(auto_now_add=True) # set once on creation
    updated_at  = models.DateTimeField(auto_now=True)     # updates on every save

    def __str__(self):
        return f'{self.name} (owner: {self.owner.username})'

    class Meta:
        verbose_name        = 'Server'
        verbose_name_plural = 'Servers'
        ordering            = ['-created_at'] # newest servers first


class ServerMemberRole(models.TextChoices):
    OWNER     = 'owner',     'Owner'
    ADMIN     = 'admin',     'Admin'
    MODERATOR = 'moderator', 'Moderator'
    MEMBER    = 'member',    'Member'


class ServerMember(models.Model):
    server    = models.ForeignKey(
                    Server,
                    on_delete=models.CASCADE,   # remove member if server deleted
                    related_name='members'
                )
    user      = models.ForeignKey(
                    settings.AUTH_USER_MODEL,
                    on_delete=models.CASCADE,   # remove membership if user deleted
                    related_name='server_memberships'
                )
    role      = models.CharField(
                    max_length=10,
                    choices=ServerMemberRole.choices,
                    default=ServerMemberRole.MEMBER
                )
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} in {self.server.name} as {self.role}'

    class Meta:
        verbose_name        = 'Server Member'
        verbose_name_plural = 'Server Members'
        ordering            = ['joined_at']
        unique_together     = ['server', 'user'] # user can only join a server once


# ── NEW — Server Ban ─────────────────────────────────────
class ServerBan(models.Model):
    # WHY a separate model instead of just deleting ServerMember →
    # kicking removes the membership row, but banning needs to be
    # remembered PERMANENTLY so the user can't just rejoin with the
    # invite code five seconds later. ServerMember alone can't do that.
    server    = models.ForeignKey(
                    Server,
                    on_delete=models.CASCADE,
                    related_name='bans'
                )
    user      = models.ForeignKey(
                    settings.AUTH_USER_MODEL,
                    on_delete=models.CASCADE,
                    related_name='server_bans'
                )
    banned_by = models.ForeignKey(
                    settings.AUTH_USER_MODEL,
                    on_delete=models.SET_NULL,
                    null=True,
                    related_name='bans_issued'
                )
    reason    = models.CharField(max_length=255, null=True, blank=True)
    banned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} banned from {self.server.name}'

    class Meta:
        verbose_name        = 'Server Ban'
        verbose_name_plural = 'Server Bans'
        unique_together     = ['server', 'user']  # can't double-ban the same user