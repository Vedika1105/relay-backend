from django.contrib.auth.models import AbstractUser
from django.db import models


class UserStatus(models.TextChoices):
    # variable    DB value    Admin label
    ONLINE  = 'online',  'Online'
    OFFLINE = 'offline', 'Offline'
    IDLE    = 'idle',    'Idle'
    DND     = 'dnd',     'Do Not Disturb'


class User(AbstractUser):
    # AbstractUser already has: username, email, password,
    # first_name, last_name, is_active, is_staff, date_joined

    display_name = models.CharField(max_length=50, null=True, blank=True)        # nickname in servers
    bio          = models.TextField(max_length=200, null=True, blank=True)        # profile bio
    avatar       = models.ImageField(upload_to='avatars/', null=True, blank=True) # profile picture
    status       = models.CharField(max_length=10, choices=UserStatus.choices, default=UserStatus.OFFLINE) # online/offline/idle/dnd
    is_email_verified = models.BooleanField(default=False)
    last_seen    = models.DateTimeField(null=True, blank=True)                    # last active time
    updated_at   = models.DateTimeField(auto_now=True)                            # updates on every save
    email        = models.EmailField(unique=True)                                 # override → no duplicate emails

    def __str__(self):
        return f'{self.username} ({self.email})'

    class Meta:
        verbose_name        = 'User'
        verbose_name_plural = 'Users'
        ordering            = ['-date_joined'] # newest users first