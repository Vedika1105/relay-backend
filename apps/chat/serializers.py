from rest_framework import serializers
from .models        import Channel, ChannelPermission


class ChannelSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    server_name         = serializers.CharField(source='server.name', read_only=True)

    class Meta:
        model  = Channel
        fields = ['id', 'name', 'description', 'channel_type',
                  'server_name', 'created_by_username',
                  'is_private', 'created_at']
        read_only_fields = ['id', 'created_at']


class CreateChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Channel
        fields = ['name', 'description', 'channel_type', 'is_private']

    def validate_name(self, value):
      import re
      if not re.match(r'^[a-z0-9_\- ]{1,100}$', value):
          raise serializers.ValidationError(
              'Channel name must be lowercase letters, numbers, hyphens, underscores or spaces only.'
          )
      return value


# ── NEW — Channel Permission Override ─────────────────────
class ChannelPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ChannelPermission
        fields = ['id', 'role', 'can_read', 'can_write']