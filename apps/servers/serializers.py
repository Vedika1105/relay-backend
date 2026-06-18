from rest_framework      import serializers
from .models             import Server, ServerMember, ServerMemberRole, ServerBan
from django.conf         import settings


class ServerMemberSerializer(serializers.ModelSerializer):
    username     = serializers.CharField(source='user.username', read_only=True)
    display_name = serializers.CharField(source='user.display_name', read_only=True)
    avatar       = serializers.ImageField(source='user.avatar', read_only=True)
    status       = serializers.CharField(source='user.status', read_only=True)
    user_id      = serializers.IntegerField(source='user.id', read_only=True)  

    class Meta:
        model  = ServerMember
        fields = ['id', 'user_id', 'username', 'display_name', 'avatar', 'status', 'role', 'joined_at']


class ServerSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    member_count   = serializers.SerializerMethodField()

    class Meta:
        model  = Server
        fields = ['id', 'name', 'description', 'icon', 'invite_code',
                  'owner_username', 'member_count', 'created_at']
        read_only_fields = ['id', 'invite_code', 'created_at']

    def get_member_count(self, obj):
        return obj.members.count()


class CreateServerSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Server
        fields = ['name', 'description', 'icon']

    def create(self, validated_data):
        owner = self.context['request'].user
        server = Server.objects.create(owner=owner, **validated_data)
        ServerMember.objects.create(
            server=server,
            user=owner,
            role=ServerMemberRole.OWNER
        )
        return server


class UpdateServerSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Server
        fields = ['name', 'description', 'icon']


class ServerBanSerializer(serializers.ModelSerializer):
    username            = serializers.CharField(source='user.username', read_only=True)
    banned_by_username  = serializers.CharField(source='banned_by.username', read_only=True)
    user_id             = serializers.IntegerField(source='user.id', read_only=True)  #

    class Meta:
        model  = ServerBan
        fields = ['id', 'user_id', 'username', 'banned_by_username', 'reason', 'banned_at']