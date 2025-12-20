"""
Views for notifications app
"""
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import PushSubscription
from .serializers import (
    PushSubscriptionSerializer,
    PushSubscriptionCreateSerializer
)


@extend_schema_view(
    get=extend_schema(
        operation_id='push_subscription_list',
        summary='List Push Subscriptions',
        description='Get list of push notification subscriptions for current user',
        tags=['Notifications'],
        responses={
            200: PushSubscriptionSerializer(many=True)
        }
    ),
    post=extend_schema(
        operation_id='push_subscription_create',
        summary='Subscribe to Push Notifications',
        description='Subscribe to push notifications by providing endpoint and keys',
        tags=['Notifications'],
        request=PushSubscriptionCreateSerializer,
        responses={
            201: PushSubscriptionSerializer,
            400: {'description': 'Validation error'}
        }
    )
)
class PushSubscriptionListCreateView(generics.ListCreateAPIView):
    """لیست و ایجاد subscription های Push Notification"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PushSubscriptionSerializer

    def get_queryset(self):
        """فقط subscription های کاربر فعلی"""
        return PushSubscription.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PushSubscriptionCreateSerializer
        return PushSubscriptionSerializer


@extend_schema(
    operation_id='push_subscription_delete',
    summary='Unsubscribe from Push Notifications',
    description='Remove a push notification subscription',
    tags=['Notifications'],
    responses={
        204: {'description': 'Subscription deleted successfully'},
        404: {'description': 'Subscription not found'}
    }
)
@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def unsubscribe_push_notification(request, subscription_id):
    """حذف subscription Push Notification"""
    try:
        subscription = PushSubscription.objects.get(
            id=subscription_id,
            user=request.user
        )
        subscription.delete()
        return Response(
            {'message': 'اشتراک با موفقیت حذف شد'},
            status=status.HTTP_204_NO_CONTENT
        )
    except PushSubscription.DoesNotExist:
        return Response(
            {'error': 'اشتراک یافت نشد'},
            status=status.HTTP_404_NOT_FOUND
        )


@extend_schema(
    operation_id='push_subscription_delete_by_endpoint',
    summary='Unsubscribe by Endpoint',
    description='Remove push notification subscription by endpoint',
    tags=['Notifications'],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'endpoint': {'type': 'string', 'format': 'uri'}
            },
            'required': ['endpoint']
        }
    },
    responses={
        204: {'description': 'Subscription deleted successfully'},
        400: {'description': 'Endpoint not provided'},
        404: {'description': 'Subscription not found'}
    }
)
@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def unsubscribe_by_endpoint(request):
    """حذف subscription بر اساس endpoint"""
    endpoint = request.data.get('endpoint')
    
    if not endpoint:
        return Response(
            {'error': 'endpoint الزامی است'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        subscription = PushSubscription.objects.get(
            endpoint=endpoint,
            user=request.user
        )
        subscription.delete()
        return Response(
            {'message': 'اشتراک با موفقیت حذف شد'},
            status=status.HTTP_204_NO_CONTENT
        )
    except PushSubscription.DoesNotExist:
        return Response(
            {'error': 'اشتراک یافت نشد'},
            status=status.HTTP_404_NOT_FOUND
        )


@extend_schema(
    operation_id='get_vapid_public_key',
    summary='Get VAPID Public Key',
    description='Get VAPID public key for client-side subscription',
    tags=['Notifications'],
    responses={
        200: {
            'description': 'VAPID public key',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'public_key': {'type': 'string'}
                        }
                    }
                }
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])  # VAPID public key یک اطلاعات عمومی است
def get_vapid_public_key(request):
    """دریافت VAPID Public Key"""
    from django.conf import settings
    
    webpush_settings = getattr(settings, 'WEBPUSH_SETTINGS', {})
    vapid_public_key = webpush_settings.get('VAPID_PUBLIC_KEY', '')
    
    if not vapid_public_key:
        return Response(
            {'error': 'VAPID Public Key تنظیم نشده است'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return Response({
        'public_key': vapid_public_key
    })


@extend_schema(
    operation_id='test_push_notification',
    summary='Send Test Push Notification',
    description='Send a test push notification to current user (for testing purposes)',
    tags=['Notifications'],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'title': {'type': 'string', 'default': 'تست نوتفیکیشن'},
                'body': {'type': 'string', 'default': 'این یک نوتفیکیشن تستی است'}
            }
        }
    },
    responses={
        200: {
            'description': 'Notification sent',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'message': {'type': 'string'},
                            'success_count': {'type': 'integer'},
                            'failed_count': {'type': 'integer'}
                        }
                    }
                }
            }
        },
        400: {'description': 'No subscriptions found'}
    }
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def test_push_notification(request):
    """ارسال نوتفیکیشن تستی به کاربر فعلی"""
    from apps.notifications.services import send_push_notification
    
    title = request.data.get('title', 'تست نوتفیکیشن')
    body = request.data.get('body', 'این یک نوتفیکیشن تستی است')
    
    success_count, failed_count = send_push_notification(
        user=request.user,
        title=title,
        body=body,
        data={
            'type': 'test',
            'timestamp': timezone.now().isoformat()
        }
    )
    
    if success_count == 0 and failed_count == 0:
        return Response(
            {'error': 'هیچ subscription فعالی برای شما یافت نشد. لطفاً ابتدا subscription خود را ثبت کنید.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # بررسی اینکه آیا subscription های نامعتبر حذف شدند
    remaining_subscriptions = PushSubscription.objects.filter(user=request.user).count()
    
    return Response({
        'message': f'نوتفیکیشن ارسال شد',
        'success_count': success_count,
        'failed_count': failed_count,
        'remaining_subscriptions': remaining_subscriptions,
        'note': 'اگر failed_count > 0 باشد، ممکن است subscription های نامعتبر حذف شده باشند. لطفاً دوباره subscribe کنید.' if failed_count > 0 else None
    })

