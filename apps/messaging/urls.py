from django.urls import path
from .views      import MessageHistoryView, MessageActionView, MessageAttachmentUploadView

urlpatterns = [
    path('<int:channel_id>/', MessageHistoryView.as_view(), name='message-history'),
    path('<int:channel_id>/attachment/', MessageAttachmentUploadView.as_view(), name='message-attachment-upload'),
    path('msg/<int:message_id>/', MessageActionView.as_view(), name='message-action'),
]