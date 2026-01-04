from django.urls import path
from . import views

app_name = 'hr'

urlpatterns = [
    # Announcement URLs
    path('announcements/', views.AnnouncementListView.as_view(), name='announcement-list'),
    path('announcements/my/', views.MyAnnouncementsView.as_view(), name='my-announcements'),
    path('announcements/<int:pk>/', views.AnnouncementDetailView.as_view(), name='announcement-detail'),
    path('announcements/unread-count/', views.announcement_unread_count, name='announcement-unread-count'),
    path('announcements/<int:pk>/mark-as-read/', views.announcement_mark_as_read, name='announcement-mark-as-read'),
    path('announcements/statistics/', views.announcement_statistics, name='announcement-statistics'),
    path('announcements/bulk/', views.create_bulk_announcement, name='create-bulk-announcement'),
    path('announcements/<int:pk>/publish/', views.publish_announcement, name='publish-announcement'),
    path('announcements/<int:pk>/unpublish/', views.unpublish_announcement, name='unpublish-announcement'),
    
    # Feedback URLs
    path('feedbacks/', views.FeedbackListCreateView.as_view(), name='feedback-list-create'),
    path('feedbacks/<int:pk>/', views.FeedbackDetailView.as_view(), name='feedback-detail'),
    path('feedbacks/<int:pk>/update-status/', views.update_feedback_status, name='update-feedback-status'),
    
    # Insurance Form URLs
    path('insurance-forms/', views.InsuranceFormListCreateView.as_view(), name='insurance-form-list-create'),
    path('insurance-forms/<int:pk>/', views.InsuranceFormDetailView.as_view(), name='insurance-form-detail'),
    path('insurance-forms/<int:pk>/update-status/', views.update_insurance_form_status, name='update-insurance-form-status'),
    
    # PhoneBook URLs
    path('phonebook/search/', views.phonebook_search, name='phonebook-search'),
    
    # Story URLs
    path('stories/', views.StoryListView.as_view(), name='story-list'),
    path('stories/<int:pk>/', views.StoryDetailView.as_view(), name='story-detail'),
]


