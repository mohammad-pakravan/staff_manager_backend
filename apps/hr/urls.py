from django.urls import path
from . import views

app_name = 'hr'

urlpatterns = [
    # Announcement URLs
    path('announcements/', views.AnnouncementListView.as_view(), name='announcement-list'),
    path('announcements/<int:pk>/', views.AnnouncementDetailView.as_view(), name='announcement-detail'),
    path('announcements/statistics/', views.announcement_statistics, name='announcement-statistics'),
    path('announcements/bulk/', views.create_bulk_announcement, name='create-bulk-announcement'),
    path('announcements/<int:announcement_id>/publish/', views.publish_announcement, name='publish-announcement'),
    path('announcements/<int:announcement_id>/unpublish/', views.unpublish_announcement, name='unpublish-announcement'),
]


