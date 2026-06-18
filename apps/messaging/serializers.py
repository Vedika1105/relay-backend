from rest_framework import serializers
from .models        import Message

class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    sender_avatar   = serializers.ImageField(source='sender.avatar', read_only=True)

    class Meta:
        model  = Message
        fields = ['id', 'content', 'sender_username', 'sender_avatar',
                  'is_edited', 'created_at', 'updated_at',
                  'attachment', 'attachment_name', 'attachment_size']
        read_only_fields = ['id', 'is_edited', 'created_at', 'updated_at',
                             'attachment', 'attachment_name', 'attachment_size']