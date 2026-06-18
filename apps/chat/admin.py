from django.contrib import admin
from .models import Channel


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display  = ['name', 'channel_type', 'server', 'is_private', 'created_at']
    list_filter   = ['channel_type', 'is_private']
    search_fields = ['name', 'server__name']