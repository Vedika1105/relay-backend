from django.db   import models
from django.conf import settings
from apps.servers.models import ServerMemberRole

class ChannelType(models.TextChoices):
    TEXT  = 'text',  'Text'
    VOICE = 'voice', 'Voice'
    VIDEO = 'video', 'Video'


class Channel(models.Model):
    name         = models.CharField(max_length=100)
    description  = models.TextField(max_length=500, null=True, blank=True)
    channel_type = models.CharField(
                        max_length=10,
                        choices=ChannelType.choices,
                        default=ChannelType.TEXT
                    )
    server       = models.ForeignKey(
                        'servers.Server',          # reference servers app
                        on_delete=models.CASCADE,  # delete channels if server deleted
                        related_name='channels'
                    )
    created_by   = models.ForeignKey(
                        settings.AUTH_USER_MODEL,
                        on_delete=models.SET_NULL, # keep channel even if creator deleted
                        null=True,
                        related_name='created_channels'
                    )
    is_private   = models.BooleanField(default=False) # private channels hidden from members
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.name} ({self.channel_type}) in {self.server.name}'

    class Meta:
        verbose_name        = 'Channel'
        verbose_name_plural = 'Channels'
        ordering            = ['created_at']        # oldest channels first
        unique_together     = ['server', 'name']    # no duplicate channel names in same server


# ── NEW — Channel Permission Override ─────────────────────
class ChannelPermission(models.Model):
    # WHY → is_private only controls whether a channel is visible at all.
    # This controls READ vs WRITE separately, per role, on top of that —
    # e.g. #announcements: everyone reads, only admin/owner writes.
    # Owner/Admin always bypass this (handled in permissions.py), so this
    # table only ever needs rows for moderator/member.
    channel   = models.ForeignKey(
                    Channel,
                    on_delete=models.CASCADE,
                    related_name='permission_overrides'
                )
    role      = models.CharField(max_length=10, choices=ServerMemberRole.choices)
    can_read  = models.BooleanField(default=True)
    can_write = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.channel.name} - {self.role}: read={self.can_read}, write={self.can_write}'

    class Meta:
        verbose_name        = 'Channel Permission Override'
        verbose_name_plural = 'Channel Permission Overrides'
        unique_together     = ['channel', 'role']