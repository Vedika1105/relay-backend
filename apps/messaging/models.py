from django.db   import models
from django.conf import settings


MAX_MESSAGE_LENGTH = 2000

class Message(models.Model):
    channel    = models.ForeignKey(
                    'chat.Channel',               # message belongs to a channel
                    on_delete=models.CASCADE,     # delete messages if channel deleted
                    related_name='messages'
                 )
    sender     = models.ForeignKey(
                    settings.AUTH_USER_MODEL,     # who sent the message
                    on_delete=models.CASCADE,
                    related_name='messages'
                 )
    content    = models.TextField(max_length=MAX_MESSAGE_LENGTH, blank=True)  # message text loosing content so that i can upload docs too <blank=True>
    is_edited  = models.BooleanField(default=False) # was message edited
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # ── NEW — optional file attachment ──
    attachment      = models.FileField(upload_to='attachments/', null=True, blank=True)
    attachment_name = models.CharField(max_length=255, null=True, blank=True)
    attachment_size = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f'{self.sender.username}: {self.content[:50]}'

    class Meta:
        verbose_name        = 'Message'
        verbose_name_plural = 'Messages'
        ordering            = ['created_at']