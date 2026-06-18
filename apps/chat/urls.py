from django.urls import path
from .views import ChannelListCreateView, ChannelDetailView, ChannelPermissionView

urlpatterns = [
    path('', ChannelListCreateView.as_view(), name='channel-list-create'),
    path('<int:channel_id>/',  ChannelDetailView.as_view(), name='channel-detail'),
    path('<int:channel_id>/permissions/', ChannelPermissionView.as_view(), name='channel-permissions'),
]