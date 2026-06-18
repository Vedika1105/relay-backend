from django.urls import path
from .views      import (CreateServerView, MyServersView, ServerDetailView,
                          JoinServerView, LeaveServerView, ServerMembersView,
                          UpdateMemberRoleView, KickMemberView, TransferOwnershipView,
                          BanMemberView, UnbanMemberView, ServerBansView)

urlpatterns = [
    path('',                         CreateServerView.as_view(),  name='create-server'),
    path('my/',                      MyServersView.as_view(),     name='my-servers'),
    path('<int:server_id>/',         ServerDetailView.as_view(),  name='server-detail'),
    path('<int:server_id>/leave/',   LeaveServerView.as_view(),   name='leave-server'),
    path('<int:server_id>/members/', ServerMembersView.as_view(), name='server-members'),
    path('<int:server_id>/members/<int:user_id>/role/', UpdateMemberRoleView.as_view(), name='update-member-role'),
    path('<int:server_id>/members/<int:user_id>/kick/', KickMemberView.as_view(), name='kick-member'),
    path('<int:server_id>/members/<int:user_id>/ban/', BanMemberView.as_view(), name='ban-member'),
    path('<int:server_id>/members/<int:user_id>/unban/', UnbanMemberView.as_view(), name='unban-member'),
    path('<int:server_id>/bans/', ServerBansView.as_view(), name='server-bans'),
    path('<int:server_id>/transfer-ownership/', TransferOwnershipView.as_view(), name='transfer-ownership'),
    path('join/',                    JoinServerView.as_view(),    name='join-server'),
]