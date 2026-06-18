from django.contrib import admin
from .models        import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display  = ['sender', 'channel', 'content', 'is_edited', 'created_at']
    list_filter   = ['is_edited']
    search_fields = ['sender__username', 'content']