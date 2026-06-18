from django.contrib import admin
from .models        import Server, ServerMember


@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    list_display  = ['name', 'owner', 'created_at']
    search_fields = ['name', 'owner__username']


@admin.register(ServerMember)
class ServerMemberAdmin(admin.ModelAdmin):
    list_display  = ['user', 'server', 'role', 'joined_at']
    list_filter   = ['role']
    search_fields = ['user__username', 'server__name']