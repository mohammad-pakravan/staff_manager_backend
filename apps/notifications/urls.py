"""
URL configuration for notifications app
"""
from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('subscribe/', views.PushSubscriptionListCreateView.as_view(), name='push-subscription-list-create'),
    path('unsubscribe/<int:subscription_id>/', views.unsubscribe_push_notification, name='push-subscription-delete'),
    path('unsubscribe/', views.unsubscribe_by_endpoint, name='push-subscription-delete-by-endpoint'),
    path('test/', views.test_push_notification, name='test-push-notification'),
    path('vapid-key/', views.get_vapid_public_key, name='get-vapid-public-key'),
]

