from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .models import Announcement, AnnouncementReadStatus, Feedback, InsuranceForm, PhoneBook, Story
from .serializers import (
    AnnouncementSerializer, 
    AnnouncementCreateSerializer, 
    AnnouncementListSerializer,
    FeedbackSerializer,
    FeedbackCreateSerializer,
    FeedbackUpdateSerializer,
    FirstPageImageSerializer,
    InsuranceFormSerializer,
    InsuranceFormCreateSerializer,
    InsuranceFormUpdateSerializer,
    PhoneBookSerializer,
    StorySerializer,
    StoryCreateSerializer,
    StoryListSerializer
)
from .permissions import HRPermission, HRUpdatePermission
# from apps.core.utils import get_jalali_now  # Not needed anymore
from apps.core.pagination import CustomPageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import FirstPageImage
from .serializers import FirstPageImageSerializer


@extend_schema_view(
    get=extend_schema(
        operation_id='announcement_list',
        summary='List Announcements and News',
        description='Get list of announcements and news. Regular users see active items for their centers. HR/Admin see all. Filter by is_news and is_announcement query parameters.',
        tags=['HR'],
        parameters=[
            OpenApiParameter(name='page', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description='Page number'),
            OpenApiParameter(name='page_size', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description='Page size'),
            OpenApiParameter(name='center', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description='Filter by center ID (HR/Admin only)'),
            OpenApiParameter(name='is_active', type=OpenApiTypes.BOOL, location=OpenApiParameter.QUERY, description='Filter by active status (HR/Admin only)'),
            OpenApiParameter(name='is_news', type=OpenApiTypes.BOOL, location=OpenApiParameter.QUERY, description='Filter by news (true for news only)'),
            OpenApiParameter(name='is_announcement', type=OpenApiTypes.BOOL, location=OpenApiParameter.QUERY, description='Filter by announcement (true for announcements only)'),
        ]
    ),
    post=extend_schema(
        operation_id='announcement_create',
        summary='Create Announcement or News',
        description='Create new announcement or news (only for HR and System Admin). Use is_news=true for news, is_announcement=true for announcements, or both for both.',
        tags=['HR'],
        request=AnnouncementCreateSerializer,
        responses={
            201: AnnouncementSerializer,
            400: {'description': 'Validation error'},
            403: {'description': 'Permission denied'}
        }
    )
)
class AnnouncementListView(generics.ListCreateAPIView):
    """لیست و ایجاد اطلاعیه‌ها و خبرها"""
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPageNumberPagination
    parser_classes = [JSONParser, MultiPartParser, FormParser]  # پشتیبانی از JSON و form-data برای آپلود تصویر
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AnnouncementCreateSerializer
        return AnnouncementListSerializer

    def get_queryset(self):
        user = self.request.user
        
        # ادمین سیستم و ادمین HR می‌توانند همه اطلاعیه‌ها و خبرها را ببینند (فعال و غیرفعال)
        if user.role in ['sys_admin', 'hr']:
            queryset = Announcement.objects.all().prefetch_related('centers', 'target_users')
        else:
            # کاربران عادی فقط اطلاعیه‌ها و خبرها فعال مراکز خود را می‌بینند
            # برای خبر (is_news=True): فقط بر اساس مراکز
            # برای اطلاعیه (is_announcement=True): بر اساس مراکز، send_to_all_users، یا target_users
            queryset = Announcement.objects.filter(is_active=True).prefetch_related('centers', 'target_users')
            user_centers = user.centers.all()
            
            # فیلتر برای خبر (is_news=True): فقط بر اساس مراکز
            news_filter = Q(is_news=True) & Q(centers__in=user_centers)
            
            # فیلتر برای اطلاعیه (is_announcement=True): بر اساس مراکز، send_to_all_users، یا target_users
            announcement_filter = Q(is_announcement=True) & (
                Q(centers__in=user_centers) | Q(send_to_all_users=True) | Q(target_users=user)
            )
            
            # ترکیب فیلترها: خبر یا اطلاعیه
            queryset = queryset.filter(news_filter | announcement_filter).distinct()
        
        # فیلتر بر اساس مرکز (فقط برای ادمین‌ها)
        center_id = self.request.query_params.get('center')
        if center_id and user.role in ['sys_admin', 'hr']:
            queryset = queryset.filter(centers__id=center_id).distinct()
        
        # فیلتر بر اساس وضعیت فعال/غیرفعال (فقط برای ادمین‌ها)
        is_active_param = self.request.query_params.get('is_active')
        if is_active_param is not None and user.role in ['sys_admin', 'hr']:
            is_active = is_active_param.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_active=is_active)
        
        # فیلتر بر اساس is_announcement و is_news
        is_announcement_param = self.request.query_params.get('is_announcement')
        is_news_param = self.request.query_params.get('is_news')
        
        if is_announcement_param is not None:
            is_announcement = is_announcement_param.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_announcement=is_announcement)
        if is_news_param is not None:
            is_news = is_news_param.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_news=is_news)
        
        return queryset.order_by('-publish_date')

    def perform_create(self, serializer):
        """ایجاد اطلاعیه یا خبر توسط کاربر فعلی"""
        user = self.request.user
        # فقط HR و System Admin می‌توانند اطلاعیه یا خبر ایجاد کنند
        if user.role not in ['hr', 'sys_admin']:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("فقط نیروی انسانی می‌تواند اطلاعیه یا خبر ایجاد کند")
        
        # ادمین HR و System Admin می‌توانند برای هر مرکزی اطلاعیه ایجاد کنند
        announcement = serializer.save(created_by=user)
        
        # اگر اطلاعیه با is_active=True و is_announcement=True ایجاد شد، نوتفیکیشن ارسال کن
        if announcement.is_active and announcement.is_announcement:
            from apps.notifications.services import send_push_notification_to_multiple_users
            from apps.accounts.models import User as UserModel
            
            # جمع‌آوری کاربران: از مراکز، کاربران خاص، یا همه کاربران
            users = UserModel.objects.none()
            
            # اگر send_to_all_users فعال باشد، به همه کاربران ارسال کن
            if announcement.send_to_all_users:
                users = UserModel.objects.all()
            else:
                # کاربران مراکز انتخاب شده
                announcement_centers = announcement.centers.all()
                if announcement_centers.exists():
                    center_users = UserModel.objects.filter(centers__in=announcement_centers).distinct()
                    users = users.union(center_users)
                
                # کاربران خاص انتخاب شده
                target_users = announcement.target_users.all()
                if target_users.exists():
                    users = users.union(target_users)
            
            if users.exists():
                # تبدیل به list برای distinct کردن
                user_ids = list(set(users.values_list('id', flat=True)))
                final_users = UserModel.objects.filter(id__in=user_ids)
                
                # استفاده از lead به عنوان body، اگر موجود نبود از title استفاده می‌کنیم
                notification_body = announcement.lead if announcement.lead else announcement.title
                send_push_notification_to_multiple_users(
                    users=final_users,
                    title=announcement.title,
                    body=notification_body,
                    data={
                        'type': 'announcement_published',
                        'announcement_id': announcement.id,
                        'title': announcement.title,
                    },
                    url=f'/announcements/{announcement.id}/'
                )


@extend_schema_view(
    get=extend_schema(
        operation_id='announcement_detail',
        summary='Get Announcement or News Details',
        description='Get details of a specific announcement or news. Automatically marks as read for authenticated users.',
        tags=['HR'],
        responses={
            200: AnnouncementSerializer,
            404: {'description': 'Announcement not found'}
        }
    ),
    put=extend_schema(
        operation_id='announcement_update',
        summary='Update Announcement or News',
        description='Update announcement or news completely (only for HR and System Admin)',
        tags=['HR'],
        request=AnnouncementCreateSerializer,
        responses={
            200: AnnouncementSerializer,
            400: {'description': 'Validation error'},
            403: {'description': 'Permission denied'},
            404: {'description': 'Announcement not found'}
        }
    ),
    patch=extend_schema(
        operation_id='announcement_partial_update',
        summary='Partial Update Announcement or News',
        description='Partially update announcement or news (only for HR and System Admin)',
        tags=['HR'],
        request=AnnouncementCreateSerializer,
        responses={
            200: AnnouncementSerializer,
            400: {'description': 'Validation error'},
            403: {'description': 'Permission denied'},
            404: {'description': 'Announcement not found'}
        }
    ),
    delete=extend_schema(
        operation_id='announcement_delete',
        summary='Delete Announcement or News',
        description='Delete announcement or news (only for HR and System Admin)',
        tags=['HR'],
        responses={
            204: {'description': 'Announcement deleted'},
            403: {'description': 'Permission denied'},
            404: {'description': 'Announcement not found'}
        }
    )
)
class AnnouncementDetailView(generics.RetrieveUpdateDestroyAPIView):
    """جزئیات، ویرایش و حذف اطلاعیه‌ها و خبرها"""
    serializer_class = AnnouncementSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]  # پشتیبانی از JSON و form-data برای آپلود تصویر

    def get_queryset(self):
        user = self.request.user
        
        # ادمین سیستم و ادمین HR می‌توانند همه اطلاعیه‌ها و خبرها را ببینند (فعال و غیرفعال)
        if user.role in ['sys_admin', 'hr']:
            queryset = Announcement.objects.all().prefetch_related('centers', 'target_users')
        else:
            # کاربران عادی فقط اطلاعیه‌ها و خبرها فعال مراکز خود را می‌بینند
            # برای خبر (is_news=True): فقط بر اساس مراکز
            # برای اطلاعیه (is_announcement=True): بر اساس مراکز، send_to_all_users، یا target_users
            queryset = Announcement.objects.filter(is_active=True).prefetch_related('centers', 'target_users')
            user_centers = user.centers.all()
            
            # فیلتر برای خبر (is_news=True): فقط بر اساس مراکز
            news_filter = Q(is_news=True) & Q(centers__in=user_centers)
            
            # فیلتر برای اطلاعیه (is_announcement=True): بر اساس مراکز، send_to_all_users، یا target_users
            announcement_filter = Q(is_announcement=True) & (
                Q(centers__in=user_centers) | Q(send_to_all_users=True) | Q(target_users=user)
            )
            
            # ترکیب فیلترها: خبر یا اطلاعیه
            queryset = queryset.filter(news_filter | announcement_filter).distinct()
        
        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        """نمایش جزئیات و علامت‌گذاری خودکار به عنوان خوانده شده"""
        instance = self.get_object()
        
        # اگر کاربر احراز هویت شده است، به صورت خودکار به عنوان خوانده شده علامت‌گذاری کن
        if request.user and request.user.is_authenticated:
            read_status, created = AnnouncementReadStatus.objects.get_or_create(
                announcement=instance,
                user=request.user
            )
            if not read_status.read_at:
                read_status.mark_as_read()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_update(self, serializer):
        """ویرایش اطلاعیه"""
        user = self.request.user
        # فقط HR و System Admin می‌توانند اطلاعیه ویرایش کنند
        if user.role not in ['hr', 'sys_admin']:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("فقط نیروی انسانی می‌تواند اطلاعیه ویرایش کند")
        
        # بررسی اینکه آیا is_active از False به True تغییر می‌کند
        instance = self.get_object()
        was_active = instance.is_active
        
        # ادمین HR و System Admin می‌توانند همه اطلاعیه‌ها را ویرایش کنند
        announcement = serializer.save()
        
        # اگر is_active از False به True تغییر کرد و is_announcement=True است، نوتفیکیشن ارسال کن
        if not was_active and announcement.is_active and announcement.is_announcement:
            from apps.notifications.services import send_push_notification_to_multiple_users
            from apps.accounts.models import User as UserModel
            
            # جمع‌آوری کاربران: از مراکز، کاربران خاص، یا همه کاربران
            users = UserModel.objects.none()
            
            # اگر send_to_all_users فعال باشد، به همه کاربران ارسال کن
            if announcement.send_to_all_users:
                users = UserModel.objects.all()
            else:
                # کاربران مراکز انتخاب شده
                announcement_centers = announcement.centers.all()
                if announcement_centers.exists():
                    center_users = UserModel.objects.filter(centers__in=announcement_centers).distinct()
                    users = users.union(center_users)
                
                # کاربران خاص انتخاب شده
                target_users = announcement.target_users.all()
                if target_users.exists():
                    users = users.union(target_users)
            
            if users.exists():
                # تبدیل به list برای distinct کردن
                user_ids = list(set(users.values_list('id', flat=True)))
                final_users = UserModel.objects.filter(id__in=user_ids)
                
                # استفاده از lead به عنوان body، اگر موجود نبود از title استفاده می‌کنیم
                notification_body = announcement.lead if announcement.lead else announcement.title
                send_push_notification_to_multiple_users(
                    users=final_users,
                    title=announcement.title,
                    body=notification_body,
                    data={
                        'type': 'announcement_published',
                        'announcement_id': announcement.id,
                        'title': announcement.title,
                    },
                    url=f'/announcements/{announcement.id}/'
                )

    def perform_destroy(self, instance):
        """حذف اطلاعیه"""
        user = self.request.user
        # فقط HR و System Admin می‌توانند اطلاعیه حذف کنند
        if user.role not in ['hr', 'sys_admin']:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("فقط نیروی انسانی می‌تواند اطلاعیه حذف کند")
        
        # ادمین HR و System Admin می‌توانند همه اطلاعیه‌ها را حذف کنند
        instance.delete()


@extend_schema(
    operation_id='announcement_unread_count',
    summary='Get Unread Announcements Count',
    description='Get count of unread announcements for the authenticated user (only announcements, not news)',
    tags=['HR'],
    responses={
        200: {
            'description': 'Unread count',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'unread_count': {'type': 'integer'}
                        }
                    }
                }
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def announcement_unread_count(request):
    """تعداد اطلاعیه‌های خوانده نشده کاربر فعلی (فقط اطلاعیه‌ها، نه خبرها)"""
    user = request.user
    
    # دریافت اطلاعیه‌های فعال که برای کاربر ارسال شده (از طریق مراکز یا کاربران خاص)
    user_centers = user.centers.all()
    announcements = Announcement.objects.filter(
        is_active=True,
        is_announcement=True,  # فقط اطلاعیه‌ها
    ).filter(
        Q(centers__in=user_centers) | Q(send_to_all_users=True) | Q(target_users=user)
    ).distinct()
    
    # دریافت اطلاعیه‌های خوانده شده
    read_announcement_ids = AnnouncementReadStatus.objects.filter(
        user=user,
        read_at__isnull=False
    ).values_list('announcement_id', flat=True)
    
    # تعداد اطلاعیه‌های خوانده نشده
    unread_count = announcements.exclude(id__in=read_announcement_ids).count()
    
    return Response({
        'unread_count': unread_count
    })


@extend_schema(
    operation_id='announcement_mark_as_read',
    summary='Mark Announcement as Read',
    description='Mark an announcement as read for the authenticated user',
    tags=['HR'],
    responses={
        200: {
            'description': 'Marked as read',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'message': {'type': 'string'},
                            'read_at': {'type': 'string', 'format': 'date-time'}
                        }
                    }
                }
            }
        },
        404: {'description': 'Announcement not found'}
    }
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def announcement_mark_as_read(request, pk):
    """علامت‌گذاری یک اطلاعیه/خبر به عنوان خوانده شده"""
    user = request.user
    
    # بررسی دسترسی کاربر به اطلاعیه
    user_centers = user.centers.all()
    announcement = Announcement.objects.filter(
        Q(centers__in=user_centers) | Q(send_to_all_users=True) | Q(target_users=user)
    ).filter(pk=pk).first()
    
    if not announcement:
        return Response(
            {'error': 'اطلاعیه یافت نشد یا شما دسترسی به آن ندارید'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # ایجاد یا به‌روزرسانی وضعیت خوانده شده
    read_status, created = AnnouncementReadStatus.objects.get_or_create(
        announcement=announcement,
        user=user
    )
    
    if not read_status.read_at:
        read_status.mark_as_read()
    
    from jalali_date import datetime2jalali
    read_at_jalali = datetime2jalali(read_status.read_at).strftime('%Y/%m/%d %H:%M') if read_status.read_at else None
    
    return Response({
        'message': 'اطلاعیه به عنوان خوانده شده علامت‌گذاری شد',
        'read_at': read_at_jalali
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def announcement_statistics(request):
    """آمار اطلاعیه‌ها"""
    if request.user.role not in ['hr', 'sys_admin']:
        return Response({
            'error': 'دسترسی غیرمجاز'
        }, status=status.HTTP_403_FORBIDDEN)
    
    from django.db.models import Count
    from apps.centers.models import Center
    
    stats = {
        'total_announcements': Announcement.objects.count(),
        'active_announcements': Announcement.objects.filter(is_active=True).count(),
        'announcements_by_center': [],
        'recent_announcements': []
    }
    
    # اطلاعیه‌های اخیر
    recent = Announcement.objects.filter(is_active=True).order_by('-publish_date')[:5]
    stats['recent_announcements'] = [
        {
            'id': ann.id,
            'title': ann.title,
            'centers': [c.name for c in ann.centers.all()],
            'publish_date': ann.publish_date
        }
        for ann in recent
    ]
    
    # آمار بر اساس مرکز
    center_stats = Center.objects.annotate(
        announcement_count=Count('announcements', filter=Q(announcements__is_active=True))
    ).values('name', 'announcement_count')
    
    stats['announcements_by_center'] = list(center_stats)
    
    return Response(stats)


@extend_schema(
    operation_id='create_bulk_announcement',
    summary='Create Bulk Announcement',
    description='Create announcement for all centers (only for HR and System Admin)',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'title': {'type': 'string', 'description': 'عنوان اطلاعیه'},
                'lead': {'type': 'string', 'description': 'لید خبر'},
                'content': {'type': 'string', 'description': 'متن اطلاعیه'},
                'publish_date': {'type': 'string', 'format': 'date-time', 'description': 'تاریخ انتشار'},
                'is_active': {'type': 'boolean', 'description': 'وضعیت فعال بودن'}
            },
            'required': ['title', 'content']
        }
    },
    responses={
        201: OpenApiTypes.OBJECT,
        403: OpenApiTypes.OBJECT
    },
    tags=['HR']
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_bulk_announcement(request):
    """ایجاد اطلاعیه دسته‌جمعی برای همه مراکز"""
    user = request.user
    
    # فقط HR و System Admin می‌توانند اطلاعیه دسته‌جمعی ایجاد کنند
    if user.role not in ['hr', 'sys_admin']:
        return Response({
            'error': 'دسترسی غیرمجاز'
        }, status=status.HTTP_403_FORBIDDEN)
    
    title = request.data.get('title')
    lead = request.data.get('lead', '')
    content = request.data.get('content')
    publish_date = request.data.get('publish_date')
    is_active = request.data.get('is_active', True)
    
    if not title or not content:
        return Response({
            'error': 'عنوان و متن اطلاعیه الزامی است'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # دریافت همه مراکز فعال
    from apps.centers.models import Center
    centers = Center.objects.filter(is_active=True)
    
    if not centers.exists():
        return Response({
            'error': 'هیچ مرکز فعالی وجود ندارد'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # ایجاد یک اطلاعیه برای همه مراکز
    announcement = Announcement.objects.create(
        title=title,
        lead=lead,
        content=content,
        publish_date=publish_date,
        is_active=is_active,
        created_by=user
    )
    announcement.centers.set(centers)
    
    # اگر اطلاعیه با is_active=True ایجاد شد، نوتفیکیشن ارسال کن
    if announcement.is_active:
        from apps.notifications.services import send_push_notification_to_multiple_users
        from apps.accounts.models import User as UserModel
        
        # دریافت کاربرانی که در مراکز مرتبط با اطلاعیه هستند
        users = UserModel.objects.filter(centers__in=announcement.centers.all()).distinct()
        if users.exists():
            # استفاده از lead به عنوان body، اگر موجود نبود از title استفاده می‌کنیم
            notification_body = announcement.lead if announcement.lead else announcement.title
            send_push_notification_to_multiple_users(
                users=users,
                title=announcement.title,
                body=notification_body,
                data={
                    'type': 'announcement_published',
                    'announcement_id': announcement.id,
                    'title': announcement.title,
                },
                url=f'/announcements/{announcement.id}/'
            )
    
    return Response({
        'message': f'اطلاعیه برای {centers.count()} مرکز ایجاد شد',
        'announcement': {
            'id': announcement.id,
            'title': announcement.title,
            'centers': [c.name for c in announcement.centers.all()],
            'is_active': announcement.is_active
        }
    }, status=status.HTTP_201_CREATED)


@extend_schema(
    operation_id='publish_announcement',
    summary='Publish Announcement',
    description='Publish an announcement (only for HR and System Admin)',
    tags=['HR'],
    request=None,
    responses={
        200: AnnouncementSerializer,
        403: {'description': 'Permission denied'},
        404: {'description': 'Announcement not found'}
    }
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def publish_announcement(request, pk):
    """انتشار اطلاعیه"""
    if request.user.role not in ['hr', 'sys_admin']:
        return Response({
            'error': 'دسترسی غیرمجاز'
        }, status=status.HTTP_403_FORBIDDEN)
    
    announcement = get_object_or_404(Announcement, pk=pk)
    announcement.is_active = True
    announcement.publish_date = timezone.now()
    announcement.save()
    
    # ارسال نوتفیکیشن به کاربران مراکز مرتبط با اطلاعیه
    from apps.notifications.services import send_push_notification_to_multiple_users
    from apps.accounts.models import User
    
    # دریافت کاربرانی که در مراکز مرتبط با اطلاعیه هستند
    announcement_centers = announcement.centers.all()
    if announcement_centers.exists():
        users = User.objects.filter(centers__in=announcement_centers).distinct()
        if users.exists():
            # استفاده از lead به عنوان body، اگر موجود نبود از title استفاده می‌کنیم
            notification_body = announcement.lead if announcement.lead else announcement.title
            send_push_notification_to_multiple_users(
                users=users,
                title=announcement.title,
                body=notification_body,
                data={
                    'type': 'announcement_published',
                    'announcement_id': announcement.id,
                    'title': announcement.title,
                },
                url=f'/announcements/{announcement.id}/'
            )
    
    return Response({
        'message': 'اطلاعیه با موفقیت منتشر شد',
        'announcement': AnnouncementSerializer(announcement).data
    })


@extend_schema(
    operation_id='unpublish_announcement',
    summary='Unpublish Announcement',
    description='Unpublish an announcement (only for HR and System Admin)',
    tags=['HR'],
    request=None,
    responses={
        200: AnnouncementSerializer,
        403: {'description': 'Permission denied'},
        404: {'description': 'Announcement not found'}
    }
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def unpublish_announcement(request, pk):
    """لغو انتشار اطلاعیه"""
    if request.user.role not in ['hr', 'sys_admin']:
        return Response({
            'error': 'دسترسی غیرمجاز'
        }, status=status.HTTP_403_FORBIDDEN)
    
    announcement = get_object_or_404(Announcement, pk=pk)
    announcement.is_active = False
    announcement.save()
    
    return Response({
        'message': 'انتشار اطلاعیه لغو شد',
        'announcement': AnnouncementSerializer(announcement).data
    })


# ========== Feedback Views ==========

@extend_schema_view(
    get=extend_schema(
        operation_id='feedback_list',
        summary='List Feedbacks',
        description='Get list of feedbacks (users: own feedbacks, HR: feedbacks from users in their centers)',
        tags=['HR']
    ),
    post=extend_schema(
        operation_id='feedback_create',
        summary='Create Feedback',
        description='Create new feedback (all authenticated users)',
        tags=['HR'],
        request=FeedbackCreateSerializer,
        responses={
            201: FeedbackSerializer,
            400: {'description': 'Validation error'}
        }
    )
)
class FeedbackListCreateView(generics.ListCreateAPIView):
    """لیست و ایجاد نظرات"""
    permission_classes = [HRPermission]
    pagination_class = CustomPageNumberPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return FeedbackCreateSerializer
        return FeedbackSerializer

    def get_queryset(self):
        user = self.request.user
        
        # System Admin همه نظرات را می‌بیند
        if user.role == 'sys_admin':
            return Feedback.objects.all()
        
        # HR نظرات کاربران مراکز خود را می‌بیند
        if user.role == 'hr':
            if user.centers.exists():
                # کاربرانی که حداقل یک مرکز مشترک با HR دارند
                return Feedback.objects.filter(
                    user__centers__in=user.centers.all()
                ).distinct()
            return Feedback.objects.none()
        
        # Employee فقط نظرات خود را می‌بیند
        return Feedback.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema_view(
    get=extend_schema(
        operation_id='feedback_detail',
        summary='Get Feedback Details',
        description='Get details of a specific feedback',
        tags=['HR'],
        responses={
            200: FeedbackSerializer,
            404: {'description': 'Feedback not found'}
        }
    )
)
class FeedbackDetailView(generics.RetrieveAPIView):
    """جزئیات نظر"""
    serializer_class = FeedbackSerializer
    permission_classes = [HRPermission]

    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'sys_admin':
            return Feedback.objects.all()
        
        if user.role == 'hr':
            if user.centers.exists():
                return Feedback.objects.filter(
                    user__centers__in=user.centers.all()
                ).distinct()
            return Feedback.objects.none()
        
        return Feedback.objects.filter(user=user)


@extend_schema(
    operation_id='update_feedback_status',
    summary='Update Feedback Status',
    description='Update feedback status (only HR and System Admin)',
    tags=['HR'],
    request=FeedbackUpdateSerializer,
    responses={
        200: FeedbackSerializer,
        400: {'description': 'Validation error'},
        403: {'description': 'Permission denied'},
        404: {'description': 'Feedback not found'}
    }
)
@api_view(['PUT', 'PATCH'])
@permission_classes([HRUpdatePermission])
def update_feedback_status(request, pk):
    """تغییر وضعیت نظر"""
    try:
        feedback = Feedback.objects.get(pk=pk)
    except Feedback.DoesNotExist:
        return Response({
            'error': 'نظر یافت نشد'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # بررسی دسترسی
    user = request.user
    if user.role == 'hr':
        if not user.centers.exists() or not feedback.user.centers.exists():
            return Response({
                'error': 'شما دسترسی به این نظر ندارید'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # بررسی اینکه آیا حداقل یک مرکز مشترک وجود دارد
        common_centers = feedback.user.centers.filter(id__in=user.centers.values_list('id', flat=True))
        if not common_centers.exists():
            return Response({
                'error': 'شما دسترسی به این نظر ندارید'
            }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = FeedbackUpdateSerializer(
        feedback,
        data=request.data,
        partial=request.method == 'PATCH',
        context={'request': request}
    )
    
    if serializer.is_valid():
        serializer.save()
        response_serializer = FeedbackSerializer(feedback, context={'request': request})
        return Response(response_serializer.data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ========== Insurance Form Views ==========

@extend_schema_view(
    get=extend_schema(
        operation_id='insurance_form_list',
        summary='List Insurance Forms',
        description='Get list of insurance forms (users: own forms, HR: forms from users in their centers)',
        tags=['HR']
    ),
    post=extend_schema(
        operation_id='insurance_form_create',
        summary='Create Insurance Form',
        description='Create new insurance form (all authenticated users)',
        tags=['HR'],
        request=InsuranceFormCreateSerializer,
        responses={
            201: InsuranceFormSerializer,
            400: {'description': 'Validation error'}
        }
    )
)
class InsuranceFormListCreateView(generics.ListCreateAPIView):
    """لیست و ایجاد فرم‌های بیمه"""
    permission_classes = [HRPermission]
    pagination_class = CustomPageNumberPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return InsuranceFormCreateSerializer
        return InsuranceFormSerializer

    def get_queryset(self):
        user = self.request.user
        
        # System Admin همه فرم‌ها را می‌بیند
        if user.role == 'sys_admin':
            return InsuranceForm.objects.all()
        
        # HR فرم‌های کاربران مراکز خود را می‌بیند
        if user.role == 'hr':
            if user.centers.exists():
                return InsuranceForm.objects.filter(
                    user__centers__in=user.centers.all()
                ).distinct()
            return InsuranceForm.objects.none()
        
        # Employee فقط فرم‌های خود را می‌بیند
        return InsuranceForm.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema_view(
    get=extend_schema(
        operation_id='insurance_form_detail',
        summary='Get Insurance Form Details',
        description='Get details of a specific insurance form',
        tags=['HR'],
        responses={
            200: InsuranceFormSerializer,
            404: {'description': 'Insurance form not found'}
        }
    )
)
class InsuranceFormDetailView(generics.RetrieveAPIView):
    """جزئیات فرم بیمه"""
    serializer_class = InsuranceFormSerializer
    permission_classes = [HRPermission]

    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'sys_admin':
            return InsuranceForm.objects.all()
        
        if user.role == 'hr':
            if user.centers.exists():
                return InsuranceForm.objects.filter(
                    user__centers__in=user.centers.all()
                ).distinct()
            return InsuranceForm.objects.none()
        
        return InsuranceForm.objects.filter(user=user)


@extend_schema(
    operation_id='update_insurance_form_status',
    summary='Update Insurance Form Status',
    description='Update insurance form status and review comment (only HR and System Admin)',
    tags=['HR'],
    request=InsuranceFormUpdateSerializer,
    responses={
        200: InsuranceFormSerializer,
        400: {'description': 'Validation error'},
        403: {'description': 'Permission denied'},
        404: {'description': 'Insurance form not found'}
    }
)
@api_view(['PUT', 'PATCH'])
@permission_classes([HRUpdatePermission])
def update_insurance_form_status(request, pk):
    """تغییر وضعیت فرم بیمه"""
    try:
        insurance_form = InsuranceForm.objects.get(pk=pk)
    except InsuranceForm.DoesNotExist:
        return Response({
            'error': 'فرم بیمه یافت نشد'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # بررسی دسترسی
    user = request.user
    if user.role == 'hr':
        if not user.centers.exists() or not insurance_form.user.centers.exists():
            return Response({
                'error': 'شما دسترسی به این فرم بیمه ندارید'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # بررسی اینکه آیا حداقل یک مرکز مشترک وجود دارد
        common_centers = insurance_form.user.centers.filter(id__in=user.centers.values_list('id', flat=True))
        if not common_centers.exists():
            return Response({
                'error': 'شما دسترسی به این فرم بیمه ندارید'
            }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = InsuranceFormUpdateSerializer(
        insurance_form,
        data=request.data,
        partial=request.method == 'PATCH',
        context={'request': request}
    )
    
    if serializer.is_valid():
        serializer.save()
        response_serializer = InsuranceFormSerializer(insurance_form, context={'request': request})
        return Response(response_serializer.data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ========== PhoneBook Views ==========

@extend_schema(
    operation_id='phonebook_search',
    summary='Search PhoneBook',
    description='Search phonebook entries by title or phone number. All authenticated users can search.',
    tags=['HR'],
    parameters=[
        {
            'name': 'search',
            'in': 'query',
            'description': 'جستجو در عنوان یا شماره تلفن',
            'required': False,
            'schema': {'type': 'string'}
        }
    ],
    responses={
        200: PhoneBookSerializer(many=True),
        400: {'description': 'Validation error'}
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def phonebook_search(request):
    """جستجو در دفترچه تلفن"""
    search_query = request.query_params.get('search', '').strip()
    
    queryset = PhoneBook.objects.all()
    
    if search_query:
        # جستجو در عنوان و شماره تلفن
        queryset = queryset.filter(
            Q(title__icontains=search_query) | Q(phone__icontains=search_query)
        )
    
    serializer = PhoneBookSerializer(queryset, many=True, context={'request': request})
    return Response(serializer.data)


# ========== Story Views ==========

@extend_schema_view(
    get=extend_schema(
        operation_id='story_list',
        summary='List Stories',
        description='Get list of stories. All authenticated users (employees, admins, HR) can view active stories. HR and System Admin can see all stories (active and inactive).',
        tags=['HR']
    ),
    post=extend_schema(
        operation_id='story_create',
        summary='Create Story',
        description='Create new story. Only HR and System Admin can create stories.',
        tags=['HR'],
        request=StoryCreateSerializer,
        responses={
            201: StorySerializer,
            400: {'description': 'Validation error'},
            403: {'description': 'Permission denied. Only HR and System Admin can create stories.'}
        }
    )
)
class StoryListView(generics.ListCreateAPIView):
    """لیست و ایجاد استوری‌ها"""
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPageNumberPagination
    parser_classes = [JSONParser, MultiPartParser, FormParser]  # پشتیبانی از JSON و form-data برای آپلود فایل
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return StoryCreateSerializer
        return StoryListSerializer

    def get_queryset(self):
        user = self.request.user
        
        # ادمین سیستم و ادمین HR می‌توانند همه استوری‌ها را ببینند (فعال و غیرفعال)
        if user.role in ['sys_admin', 'hr']:
            queryset = Story.objects.all().select_related('created_by')
            
            # فیلتر بر اساس وضعیت فعال/غیرفعال (فقط برای ادمین‌ها)
            is_active_param = self.request.query_params.get('is_active')
            if is_active_param is not None:
                is_active = is_active_param.lower() in ['true', '1', 'yes']
                queryset = queryset.filter(is_active=is_active)
        else:
            # همه کاربران احراز هویت شده (کارمند، ادمین غذا و ...) می‌توانند استوری‌های فعال را ببینند
            queryset = Story.objects.filter(is_active=True).select_related('created_by')
        
        # فیلتر کردن استوری‌های منقضی شده - فقط استوری‌هایی که فایل دارند نمایش داده شوند
        queryset = queryset.filter(
            Q(expiry_date__isnull=True) | Q(expiry_date__gt=timezone.now())
        ).filter(
            # فقط استوری‌هایی که حداقل یکی از فایل‌ها را دارند
            Q(thumbnail_image__isnull=False) | Q(content_file__isnull=False)
        )
        
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        """ایجاد استوری توسط کاربر فعلی"""
        # بررسی دسترسی: فقط HR و System Admin می‌توانند استوری ایجاد کنند
        user = self.request.user
        if user.role not in ['hr', 'sys_admin']:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("فقط ادمین نیروی انسانی و ادمین سیستم می‌توانند استوری ایجاد کنند")
        
        serializer.save(created_by=user)


@extend_schema_view(
    get=extend_schema(
        operation_id='story_detail',
        summary='Get Story Details',
        description='Get story details. All authenticated users (employees, admins, HR) can view active story details. HR and System Admin can view all story details (active and inactive).',
        tags=['HR'],
        responses={
            200: StorySerializer,
            404: {'description': 'Story not found'}
        }
    ),
    put=extend_schema(
        operation_id='story_update',
        summary='Update Story',
        description='Update story. Only HR and System Admin can update stories.',
        tags=['HR'],
        request=StoryCreateSerializer,
        responses={
            200: StorySerializer,
            400: {'description': 'Validation error'},
            403: {'description': 'Permission denied. Only HR and System Admin can update stories.'},
            404: {'description': 'Story not found'}
        }
    ),
    patch=extend_schema(
        operation_id='story_partial_update',
        summary='Partial Update Story',
        description='Partially update story. Only HR and System Admin can update stories.',
        tags=['HR'],
        request=StoryCreateSerializer,
        responses={
            200: StorySerializer,
            400: {'description': 'Validation error'},
            403: {'description': 'Permission denied. Only HR and System Admin can update stories.'},
            404: {'description': 'Story not found'}
        }
    ),
    delete=extend_schema(
        operation_id='story_delete',
        summary='Delete Story',
        description='Delete story. Only HR and System Admin can delete stories.',
        tags=['HR'],
        responses={
            204: {'description': 'Story deleted successfully'},
            403: {'description': 'Permission denied. Only HR and System Admin can delete stories.'},
            404: {'description': 'Story not found'}
        }
    )
)
class StoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """جزئیات استوری"""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return StoryCreateSerializer
        return StorySerializer

    def get_queryset(self):
        user = self.request.user
        
        # ادمین سیستم و ادمین HR می‌توانند همه استوری‌ها را ببینند (فعال و غیرفعال)
        if user.role in ['sys_admin', 'hr']:
            queryset = Story.objects.all().select_related('created_by')
        else:
            # همه کاربران احراز هویت شده (کارمند، ادمین غذا و ...) می‌توانند استوری‌های فعال را ببینند
            queryset = Story.objects.filter(is_active=True).select_related('created_by')
        
        # فیلتر کردن استوری‌های منقضی شده - فقط استوری‌هایی که فایل دارند نمایش داده شوند
        queryset = queryset.filter(
            Q(expiry_date__isnull=True) | Q(expiry_date__gt=timezone.now())
        ).filter(
            # فقط استوری‌هایی که حداقل یکی از فایل‌ها را دارند
            Q(thumbnail_image__isnull=False) | Q(content_file__isnull=False)
        )
        
        return queryset
    
    def update(self, request, *args, **kwargs):
        """به‌روزرسانی استوری"""
        # بررسی دسترسی: فقط HR و System Admin می‌توانند استوری را به‌روزرسانی کنند
        user = request.user
        if user.role not in ['hr', 'sys_admin']:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("فقط ادمین نیروی انسانی و ادمین سیستم می‌توانند استوری را ویرایش کنند")
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """حذف استوری"""
        # بررسی دسترسی: فقط HR و System Admin می‌توانند استوری را حذف کنند
        user = request.user
        if user.role not in ['hr', 'sys_admin']:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("فقط ادمین نیروی انسانی و ادمین سیستم می‌توانند استوری را حذف کنند")
        
        return super().destroy(request, *args, **kwargs)







from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .models import Announcement, AnnouncementReadStatus, Feedback, InsuranceForm, PhoneBook, Story
from .serializers import (
    AnnouncementSerializer, 
    AnnouncementCreateSerializer, 
    AnnouncementListSerializer,
    FeedbackSerializer,
    FeedbackCreateSerializer,
    FeedbackUpdateSerializer,
    InsuranceFormSerializer,
    InsuranceFormCreateSerializer,
    InsuranceFormUpdateSerializer,
    PhoneBookSerializer,
    StorySerializer,
    StoryCreateSerializer,
    StoryListSerializer
)
from .permissions import HRPermission, HRUpdatePermission
# from apps.core.utils import get_jalali_now  # Not needed anymore
from apps.core.pagination import CustomPageNumberPagination


@extend_schema_view(
    get=extend_schema(
        operation_id='announcement_list',
        summary='List Announcements and News',
        description='Get list of announcements and news. Regular users see active items for their centers. HR/Admin see all. Filter by is_news and is_announcement query parameters.',
        tags=['HR'],
        parameters=[
            OpenApiParameter(name='page', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description='Page number'),
            OpenApiParameter(name='page_size', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description='Page size'),
            OpenApiParameter(name='center', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description='Filter by center ID (HR/Admin only)'),
            OpenApiParameter(name='is_active', type=OpenApiTypes.BOOL, location=OpenApiParameter.QUERY, description='Filter by active status (HR/Admin only)'),
            OpenApiParameter(name='is_news', type=OpenApiTypes.BOOL, location=OpenApiParameter.QUERY, description='Filter by news (true for news only)'),
            OpenApiParameter(name='is_announcement', type=OpenApiTypes.BOOL, location=OpenApiParameter.QUERY, description='Filter by announcement (true for announcements only)'),
        ]
    ),
    post=extend_schema(
        operation_id='announcement_create',
        summary='Create Announcement or News',
        description='Create new announcement or news (only for HR and System Admin). Use is_news=true for news, is_announcement=true for announcements, or both for both.',
        tags=['HR'],
        request=AnnouncementCreateSerializer,
        responses={
            201: AnnouncementSerializer,
            400: {'description': 'Validation error'},
            403: {'description': 'Permission denied'}
        }
    )
)
class AnnouncementListView(generics.ListCreateAPIView):
    """لیست و ایجاد اطلاعیه‌ها و خبرها"""
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPageNumberPagination
    parser_classes = [JSONParser, MultiPartParser, FormParser]  # پشتیبانی از JSON و form-data برای آپلود تصویر
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AnnouncementCreateSerializer
        return AnnouncementListSerializer

    def get_queryset(self):
        user = self.request.user
        
        # ادمین سیستم و ادمین HR می‌توانند همه اطلاعیه‌ها و خبرها را ببینند (فعال و غیرفعال)
        if user.role in ['sys_admin', 'hr']:
            queryset = Announcement.objects.all().prefetch_related('centers', 'target_users')
        else:
            # کاربران عادی فقط اطلاعیه‌ها و خبرها فعال مراکز خود را می‌بینند
            # برای خبر (is_news=True): فقط بر اساس مراکز
            # برای اطلاعیه (is_announcement=True): بر اساس مراکز، send_to_all_users، یا target_users
            queryset = Announcement.objects.filter(is_active=True).prefetch_related('centers', 'target_users')
            user_centers = user.centers.all()
            
            # فیلتر برای خبر (is_news=True): فقط بر اساس مراکز
            news_filter = Q(is_news=True) & Q(centers__in=user_centers)
            
            # فیلتر برای اطلاعیه (is_announcement=True): بر اساس مراکز، send_to_all_users، یا target_users
            announcement_filter = Q(is_announcement=True) & (
                Q(centers__in=user_centers) | Q(send_to_all_users=True) | Q(target_users=user)
            )
            
            # ترکیب فیلترها: خبر یا اطلاعیه
            queryset = queryset.filter(news_filter | announcement_filter).distinct()
        
        # فیلتر بر اساس مرکز (فقط برای ادمین‌ها)
        center_id = self.request.query_params.get('center')
        if center_id and user.role in ['sys_admin', 'hr']:
            queryset = queryset.filter(centers__id=center_id).distinct()
        
        # فیلتر بر اساس وضعیت فعال/غیرفعال (فقط برای ادمین‌ها)
        is_active_param = self.request.query_params.get('is_active')
        if is_active_param is not None and user.role in ['sys_admin', 'hr']:
            is_active = is_active_param.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_active=is_active)
        
        # فیلتر بر اساس is_announcement و is_news
        is_announcement_param = self.request.query_params.get('is_announcement')
        is_news_param = self.request.query_params.get('is_news')
        
        if is_announcement_param is not None:
            is_announcement = is_announcement_param.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_announcement=is_announcement)
        if is_news_param is not None:
            is_news = is_news_param.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_news=is_news)
        
        return queryset.order_by('-publish_date')

    def perform_create(self, serializer):
        """ایجاد اطلاعیه یا خبر توسط کاربر فعلی"""
        user = self.request.user
        # فقط HR و System Admin می‌توانند اطلاعیه یا خبر ایجاد کنند
        if user.role not in ['hr', 'sys_admin']:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("فقط نیروی انسانی می‌تواند اطلاعیه یا خبر ایجاد کند")
        
        # ادمین HR و System Admin می‌توانند برای هر مرکزی اطلاعیه ایجاد کنند
        announcement = serializer.save(created_by=user)
        
        # اگر اطلاعیه با is_active=True و is_announcement=True ایجاد شد، نوتفیکیشن ارسال کن
        if announcement.is_active and announcement.is_announcement:
            from apps.notifications.services import send_push_notification_to_multiple_users
            from apps.accounts.models import User as UserModel
            
            # جمع‌آوری کاربران: از مراکز، کاربران خاص، یا همه کاربران
            users = UserModel.objects.none()
            
            # اگر send_to_all_users فعال باشد، به همه کاربران ارسال کن
            if announcement.send_to_all_users:
                users = UserModel.objects.all()
            else:
                # کاربران مراکز انتخاب شده
                announcement_centers = announcement.centers.all()
                if announcement_centers.exists():
                    center_users = UserModel.objects.filter(centers__in=announcement_centers).distinct()
                    users = users.union(center_users)
                
                # کاربران خاص انتخاب شده
                target_users = announcement.target_users.all()
                if target_users.exists():
                    users = users.union(target_users)
            
            if users.exists():
                # تبدیل به list برای distinct کردن
                user_ids = list(set(users.values_list('id', flat=True)))
                final_users = UserModel.objects.filter(id__in=user_ids)
                
                # استفاده از lead به عنوان body، اگر موجود نبود از title استفاده می‌کنیم
                notification_body = announcement.lead if announcement.lead else announcement.title
                send_push_notification_to_multiple_users(
                    users=final_users,
                    title=announcement.title,
                    body=notification_body,
                    data={
                        'type': 'announcement_published',
                        'announcement_id': announcement.id,
                        'title': announcement.title,
                    },
                    url=f'/announcements/{announcement.id}/'
                )


@extend_schema_view(
    get=extend_schema(
        operation_id='announcement_detail',
        summary='Get Announcement or News Details',
        description='Get details of a specific announcement or news. Automatically marks as read for authenticated users.',
        tags=['HR'],
        responses={
            200: AnnouncementSerializer,
            404: {'description': 'Announcement not found'}
        }
    ),
    put=extend_schema(
        operation_id='announcement_update',
        summary='Update Announcement or News',
        description='Update announcement or news completely (only for HR and System Admin)',
        tags=['HR'],
        request=AnnouncementCreateSerializer,
        responses={
            200: AnnouncementSerializer,
            400: {'description': 'Validation error'},
            403: {'description': 'Permission denied'},
            404: {'description': 'Announcement not found'}
        }
    ),
    patch=extend_schema(
        operation_id='announcement_partial_update',
        summary='Partial Update Announcement or News',
        description='Partially update announcement or news (only for HR and System Admin)',
        tags=['HR'],
        request=AnnouncementCreateSerializer,
        responses={
            200: AnnouncementSerializer,
            400: {'description': 'Validation error'},
            403: {'description': 'Permission denied'},
            404: {'description': 'Announcement not found'}
        }
    ),
    delete=extend_schema(
        operation_id='announcement_delete',
        summary='Delete Announcement or News',
        description='Delete announcement or news (only for HR and System Admin)',
        tags=['HR'],
        responses={
            204: {'description': 'Announcement deleted'},
            403: {'description': 'Permission denied'},
            404: {'description': 'Announcement not found'}
        }
    )
)
class AnnouncementDetailView(generics.RetrieveUpdateDestroyAPIView):
    """جزئیات، ویرایش و حذف اطلاعیه‌ها و خبرها"""
    serializer_class = AnnouncementSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]  # پشتیبانی از JSON و form-data برای آپلود تصویر

    def get_queryset(self):
        user = self.request.user
        
        # ادمین سیستم و ادمین HR می‌توانند همه اطلاعیه‌ها و خبرها را ببینند (فعال و غیرفعال)
        if user.role in ['sys_admin', 'hr']:
            queryset = Announcement.objects.all().prefetch_related('centers', 'target_users')
        else:
            # کاربران عادی فقط اطلاعیه‌ها و خبرها فعال مراکز خود را می‌بینند
            # برای خبر (is_news=True): فقط بر اساس مراکز
            # برای اطلاعیه (is_announcement=True): بر اساس مراکز، send_to_all_users، یا target_users
            queryset = Announcement.objects.filter(is_active=True).prefetch_related('centers', 'target_users')
            user_centers = user.centers.all()
            
            # فیلتر برای خبر (is_news=True): فقط بر اساس مراکز
            news_filter = Q(is_news=True) & Q(centers__in=user_centers)
            
            # فیلتر برای اطلاعیه (is_announcement=True): بر اساس مراکز، send_to_all_users، یا target_users
            announcement_filter = Q(is_announcement=True) & (
                Q(centers__in=user_centers) | Q(send_to_all_users=True) | Q(target_users=user)
            )
            
            # ترکیب فیلترها: خبر یا اطلاعیه
            queryset = queryset.filter(news_filter | announcement_filter).distinct()
        
        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        """نمایش جزئیات و علامت‌گذاری خودکار به عنوان خوانده شده"""
        instance = self.get_object()
        
        # اگر کاربر احراز هویت شده است، به صورت خودکار به عنوان خوانده شده علامت‌گذاری کن
        if request.user and request.user.is_authenticated:
            read_status, created = AnnouncementReadStatus.objects.get_or_create(
                announcement=instance,
                user=request.user
            )
            if not read_status.read_at:
                read_status.mark_as_read()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_update(self, serializer):
        """ویرایش اطلاعیه"""
        user = self.request.user
        # فقط HR و System Admin می‌توانند اطلاعیه ویرایش کنند
        if user.role not in ['hr', 'sys_admin']:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("فقط نیروی انسانی می‌تواند اطلاعیه ویرایش کند")
        
        # بررسی اینکه آیا is_active از False به True تغییر می‌کند
        instance = self.get_object()
        was_active = instance.is_active
        
        # ادمین HR و System Admin می‌توانند همه اطلاعیه‌ها را ویرایش کنند
        announcement = serializer.save()
        
        # اگر is_active از False به True تغییر کرد و is_announcement=True است، نوتفیکیشن ارسال کن
        if not was_active and announcement.is_active and announcement.is_announcement:
            from apps.notifications.services import send_push_notification_to_multiple_users
            from apps.accounts.models import User as UserModel
            
            # جمع‌آوری کاربران: از مراکز، کاربران خاص، یا همه کاربران
            users = UserModel.objects.none()
            
            # اگر send_to_all_users فعال باشد، به همه کاربران ارسال کن
            if announcement.send_to_all_users:
                users = UserModel.objects.all()
            else:
                # کاربران مراکز انتخاب شده
                announcement_centers = announcement.centers.all()
                if announcement_centers.exists():
                    center_users = UserModel.objects.filter(centers__in=announcement_centers).distinct()
                    users = users.union(center_users)
                
                # کاربران خاص انتخاب شده
                target_users = announcement.target_users.all()
                if target_users.exists():
                    users = users.union(target_users)
            
            if users.exists():
                # تبدیل به list برای distinct کردن
                user_ids = list(set(users.values_list('id', flat=True)))
                final_users = UserModel.objects.filter(id__in=user_ids)
                
                # استفاده از lead به عنوان body، اگر موجود نبود از title استفاده می‌کنیم
                notification_body = announcement.lead if announcement.lead else announcement.title
                send_push_notification_to_multiple_users(
                    users=final_users,
                    title=announcement.title,
                    body=notification_body,
                    data={
                        'type': 'announcement_published',
                        'announcement_id': announcement.id,
                        'title': announcement.title,
                    },
                    url=f'/announcements/{announcement.id}/'
                )

    def perform_destroy(self, instance):
        """حذف اطلاعیه"""
        user = self.request.user
        # فقط HR و System Admin می‌توانند اطلاعیه حذف کنند
        if user.role not in ['hr', 'sys_admin']:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("فقط نیروی انسانی می‌تواند اطلاعیه حذف کند")
        
        # ادمین HR و System Admin می‌توانند همه اطلاعیه‌ها را حذف کنند
        instance.delete()


@extend_schema(
    operation_id='announcement_unread_count',
    summary='Get Unread Announcements Count',
    description='Get count of unread announcements for the authenticated user (only announcements, not news)',
    tags=['HR'],
    responses={
        200: {
            'description': 'Unread count',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'unread_count': {'type': 'integer'}
                        }
                    }
                }
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def announcement_unread_count(request):
    """تعداد اطلاعیه‌های خوانده نشده کاربر فعلی (فقط اطلاعیه‌ها، نه خبرها)"""
    user = request.user
    
    # دریافت اطلاعیه‌های فعال که برای کاربر ارسال شده (از طریق مراکز یا کاربران خاص)
    user_centers = user.centers.all()
    announcements = Announcement.objects.filter(
        is_active=True,
        is_announcement=True,  # فقط اطلاعیه‌ها
    ).filter(
        Q(centers__in=user_centers) | Q(send_to_all_users=True) | Q(target_users=user)
    ).distinct()
    
    # دریافت اطلاعیه‌های خوانده شده
    read_announcement_ids = AnnouncementReadStatus.objects.filter(
        user=user,
        read_at__isnull=False
    ).values_list('announcement_id', flat=True)
    
    # تعداد اطلاعیه‌های خوانده نشده
    unread_count = announcements.exclude(id__in=read_announcement_ids).count()
    
    return Response({
        'unread_count': unread_count
    })


@extend_schema(
    operation_id='announcement_mark_as_read',
    summary='Mark Announcement as Read',
    description='Mark an announcement as read for the authenticated user',
    tags=['HR'],
    responses={
        200: {
            'description': 'Marked as read',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'message': {'type': 'string'},
                            'read_at': {'type': 'string', 'format': 'date-time'}
                        }
                    }
                }
            }
        },
        404: {'description': 'Announcement not found'}
    }
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def announcement_mark_as_read(request, pk):
    """علامت‌گذاری یک اطلاعیه/خبر به عنوان خوانده شده"""
    user = request.user
    
    # بررسی دسترسی کاربر به اطلاعیه
    user_centers = user.centers.all()
    announcement = Announcement.objects.filter(
        Q(centers__in=user_centers) | Q(send_to_all_users=True) | Q(target_users=user)
    ).filter(pk=pk).first()
    
    if not announcement:
        return Response(
            {'error': 'اطلاعیه یافت نشد یا شما دسترسی به آن ندارید'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # ایجاد یا به‌روزرسانی وضعیت خوانده شده
    read_status, created = AnnouncementReadStatus.objects.get_or_create(
        announcement=announcement,
        user=user
    )
    
    if not read_status.read_at:
        read_status.mark_as_read()
    
    from jalali_date import datetime2jalali
    read_at_jalali = datetime2jalali(read_status.read_at).strftime('%Y/%m/%d %H:%M') if read_status.read_at else None
    
    return Response({
        'message': 'اطلاعیه به عنوان خوانده شده علامت‌گذاری شد',
        'read_at': read_at_jalali
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def announcement_statistics(request):
    """آمار اطلاعیه‌ها"""
    if request.user.role not in ['hr', 'sys_admin']:
        return Response({
            'error': 'دسترسی غیرمجاز'
        }, status=status.HTTP_403_FORBIDDEN)
    
    from django.db.models import Count
    from apps.centers.models import Center
    
    stats = {
        'total_announcements': Announcement.objects.count(),
        'active_announcements': Announcement.objects.filter(is_active=True).count(),
        'announcements_by_center': [],
        'recent_announcements': []
    }
    
    # اطلاعیه‌های اخیر
    recent = Announcement.objects.filter(is_active=True).order_by('-publish_date')[:5]
    stats['recent_announcements'] = [
        {
            'id': ann.id,
            'title': ann.title,
            'centers': [c.name for c in ann.centers.all()],
            'publish_date': ann.publish_date
        }
        for ann in recent
    ]
    
    # آمار بر اساس مرکز
    center_stats = Center.objects.annotate(
        announcement_count=Count('announcements', filter=Q(announcements__is_active=True))
    ).values('name', 'announcement_count')
    
    stats['announcements_by_center'] = list(center_stats)
    
    return Response(stats)


@extend_schema(
    operation_id='create_bulk_announcement',
    summary='Create Bulk Announcement',
    description='Create announcement for all centers (only for HR and System Admin)',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'title': {'type': 'string', 'description': 'عنوان اطلاعیه'},
                'lead': {'type': 'string', 'description': 'لید خبر'},
                'content': {'type': 'string', 'description': 'متن اطلاعیه'},
                'publish_date': {'type': 'string', 'format': 'date-time', 'description': 'تاریخ انتشار'},
                'is_active': {'type': 'boolean', 'description': 'وضعیت فعال بودن'}
            },
            'required': ['title', 'content']
        }
    },
    responses={
        201: OpenApiTypes.OBJECT,
        403: OpenApiTypes.OBJECT
    },
    tags=['HR']
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_bulk_announcement(request):
    """ایجاد اطلاعیه دسته‌جمعی برای همه مراکز"""
    user = request.user
    
    # فقط HR و System Admin می‌توانند اطلاعیه دسته‌جمعی ایجاد کنند
    if user.role not in ['hr', 'sys_admin']:
        return Response({
            'error': 'دسترسی غیرمجاز'
        }, status=status.HTTP_403_FORBIDDEN)
    
    title = request.data.get('title')
    lead = request.data.get('lead', '')
    content = request.data.get('content')
    publish_date = request.data.get('publish_date')
    is_active = request.data.get('is_active', True)
    
    if not title or not content:
        return Response({
            'error': 'عنوان و متن اطلاعیه الزامی است'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # دریافت همه مراکز فعال
    from apps.centers.models import Center
    centers = Center.objects.filter(is_active=True)
    
    if not centers.exists():
        return Response({
            'error': 'هیچ مرکز فعالی وجود ندارد'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # ایجاد یک اطلاعیه برای همه مراکز
    announcement = Announcement.objects.create(
        title=title,
        lead=lead,
        content=content,
        publish_date=publish_date,
        is_active=is_active,
        created_by=user
    )
    announcement.centers.set(centers)
    
    # اگر اطلاعیه با is_active=True ایجاد شد، نوتفیکیشن ارسال کن
    if announcement.is_active:
        from apps.notifications.services import send_push_notification_to_multiple_users
        from apps.accounts.models import User as UserModel
        
        # دریافت کاربرانی که در مراکز مرتبط با اطلاعیه هستند
        users = UserModel.objects.filter(centers__in=announcement.centers.all()).distinct()
        if users.exists():
            # استفاده از lead به عنوان body، اگر موجود نبود از title استفاده می‌کنیم
            notification_body = announcement.lead if announcement.lead else announcement.title
            send_push_notification_to_multiple_users(
                users=users,
                title=announcement.title,
                body=notification_body,
                data={
                    'type': 'announcement_published',
                    'announcement_id': announcement.id,
                    'title': announcement.title,
                },
                url=f'/announcements/{announcement.id}/'
            )
    
    return Response({
        'message': f'اطلاعیه برای {centers.count()} مرکز ایجاد شد',
        'announcement': {
            'id': announcement.id,
            'title': announcement.title,
            'centers': [c.name for c in announcement.centers.all()],
            'is_active': announcement.is_active
        }
    }, status=status.HTTP_201_CREATED)


@extend_schema(
    operation_id='publish_announcement',
    summary='Publish Announcement',
    description='Publish an announcement (only for HR and System Admin)',
    tags=['HR'],
    request=None,
    responses={
        200: AnnouncementSerializer,
        403: {'description': 'Permission denied'},
        404: {'description': 'Announcement not found'}
    }
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def publish_announcement(request, pk):
    """انتشار اطلاعیه"""
    if request.user.role not in ['hr', 'sys_admin']:
        return Response({
            'error': 'دسترسی غیرمجاز'
        }, status=status.HTTP_403_FORBIDDEN)
    
    announcement = get_object_or_404(Announcement, pk=pk)
    announcement.is_active = True
    announcement.publish_date = timezone.now()
    announcement.save()
    
    # ارسال نوتفیکیشن به کاربران مراکز مرتبط با اطلاعیه
    from apps.notifications.services import send_push_notification_to_multiple_users
    from apps.accounts.models import User
    
    # دریافت کاربرانی که در مراکز مرتبط با اطلاعیه هستند
    announcement_centers = announcement.centers.all()
    if announcement_centers.exists():
        users = User.objects.filter(centers__in=announcement_centers).distinct()
        if users.exists():
            # استفاده از lead به عنوان body، اگر موجود نبود از title استفاده می‌کنیم
            notification_body = announcement.lead if announcement.lead else announcement.title
            send_push_notification_to_multiple_users(
                users=users,
                title=announcement.title,
                body=notification_body,
                data={
                    'type': 'announcement_published',
                    'announcement_id': announcement.id,
                    'title': announcement.title,
                },
                url=f'/announcements/{announcement.id}/'
            )
    
    return Response({
        'message': 'اطلاعیه با موفقیت منتشر شد',
        'announcement': AnnouncementSerializer(announcement).data
    })


@extend_schema(
    operation_id='unpublish_announcement',
    summary='Unpublish Announcement',
    description='Unpublish an announcement (only for HR and System Admin)',
    tags=['HR'],
    request=None,
    responses={
        200: AnnouncementSerializer,
        403: {'description': 'Permission denied'},
        404: {'description': 'Announcement not found'}
    }
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def unpublish_announcement(request, pk):
    """لغو انتشار اطلاعیه"""
    if request.user.role not in ['hr', 'sys_admin']:
        return Response({
            'error': 'دسترسی غیرمجاز'
        }, status=status.HTTP_403_FORBIDDEN)
    
    announcement = get_object_or_404(Announcement, pk=pk)
    announcement.is_active = False
    announcement.save()
    
    return Response({
        'message': 'انتشار اطلاعیه لغو شد',
        'announcement': AnnouncementSerializer(announcement).data
    })


# ========== Feedback Views ==========

@extend_schema_view(
    get=extend_schema(
        operation_id='feedback_list',
        summary='List Feedbacks',
        description='Get list of feedbacks (users: own feedbacks, HR: feedbacks from users in their centers)',
        tags=['HR']
    ),
    post=extend_schema(
        operation_id='feedback_create',
        summary='Create Feedback',
        description='Create new feedback (all authenticated users)',
        tags=['HR'],
        request=FeedbackCreateSerializer,
        responses={
            201: FeedbackSerializer,
            400: {'description': 'Validation error'}
        }
    )
)
class FeedbackListCreateView(generics.ListCreateAPIView):
    """لیست و ایجاد نظرات"""
    permission_classes = [HRPermission]
    pagination_class = CustomPageNumberPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return FeedbackCreateSerializer
        return FeedbackSerializer

    def get_queryset(self):
        user = self.request.user
        
        # System Admin همه نظرات را می‌بیند
        if user.role == 'sys_admin':
            return Feedback.objects.all()
        
        # HR نظرات کاربران مراکز خود را می‌بیند
        if user.role == 'hr':
            if user.centers.exists():
                # کاربرانی که حداقل یک مرکز مشترک با HR دارند
                return Feedback.objects.filter(
                    user__centers__in=user.centers.all()
                ).distinct()
            return Feedback.objects.none()
        
        # Employee فقط نظرات خود را می‌بیند
        return Feedback.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema_view(
    get=extend_schema(
        operation_id='feedback_detail',
        summary='Get Feedback Details',
        description='Get details of a specific feedback',
        tags=['HR'],
        responses={
            200: FeedbackSerializer,
            404: {'description': 'Feedback not found'}
        }
    )
)
class FeedbackDetailView(generics.RetrieveAPIView):
    """جزئیات نظر"""
    serializer_class = FeedbackSerializer
    permission_classes = [HRPermission]

    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'sys_admin':
            return Feedback.objects.all()
        
        if user.role == 'hr':
            if user.centers.exists():
                return Feedback.objects.filter(
                    user__centers__in=user.centers.all()
                ).distinct()
            return Feedback.objects.none()
        
        return Feedback.objects.filter(user=user)


@extend_schema(
    operation_id='update_feedback_status',
    summary='Update Feedback Status',
    description='Update feedback status (only HR and System Admin)',
    tags=['HR'],
    request=FeedbackUpdateSerializer,
    responses={
        200: FeedbackSerializer,
        400: {'description': 'Validation error'},
        403: {'description': 'Permission denied'},
        404: {'description': 'Feedback not found'}
    }
)
@api_view(['PUT', 'PATCH'])
@permission_classes([HRUpdatePermission])
def update_feedback_status(request, pk):
    """تغییر وضعیت نظر"""
    try:
        feedback = Feedback.objects.get(pk=pk)
    except Feedback.DoesNotExist:
        return Response({
            'error': 'نظر یافت نشد'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # بررسی دسترسی
    user = request.user
    if user.role == 'hr':
        if not user.centers.exists() or not feedback.user.centers.exists():
            return Response({
                'error': 'شما دسترسی به این نظر ندارید'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # بررسی اینکه آیا حداقل یک مرکز مشترک وجود دارد
        common_centers = feedback.user.centers.filter(id__in=user.centers.values_list('id', flat=True))
        if not common_centers.exists():
            return Response({
                'error': 'شما دسترسی به این نظر ندارید'
            }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = FeedbackUpdateSerializer(
        feedback,
        data=request.data,
        partial=request.method == 'PATCH',
        context={'request': request}
    )
    
    if serializer.is_valid():
        serializer.save()
        response_serializer = FeedbackSerializer(feedback, context={'request': request})
        return Response(response_serializer.data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ========== Insurance Form Views ==========

@extend_schema_view(
    get=extend_schema(
        operation_id='insurance_form_list',
        summary='List Insurance Forms',
        description='Get list of insurance forms (users: own forms, HR: forms from users in their centers)',
        tags=['HR']
    ),
    post=extend_schema(
        operation_id='insurance_form_create',
        summary='Create Insurance Form',
        description='Create new insurance form (all authenticated users)',
        tags=['HR'],
        request=InsuranceFormCreateSerializer,
        responses={
            201: InsuranceFormSerializer,
            400: {'description': 'Validation error'}
        }
    )
)
class InsuranceFormListCreateView(generics.ListCreateAPIView):
    """لیست و ایجاد فرم‌های بیمه"""
    permission_classes = [HRPermission]
    pagination_class = CustomPageNumberPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return InsuranceFormCreateSerializer
        return InsuranceFormSerializer

    def get_queryset(self):
        user = self.request.user
        
        # System Admin همه فرم‌ها را می‌بیند
        if user.role == 'sys_admin':
            return InsuranceForm.objects.all()
        
        # HR فرم‌های کاربران مراکز خود را می‌بیند
        if user.role == 'hr':
            if user.centers.exists():
                return InsuranceForm.objects.filter(
                    user__centers__in=user.centers.all()
                ).distinct()
            return InsuranceForm.objects.none()
        
        # Employee فقط فرم‌های خود را می‌بیند
        return InsuranceForm.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema_view(
    get=extend_schema(
        operation_id='insurance_form_detail',
        summary='Get Insurance Form Details',
        description='Get details of a specific insurance form',
        tags=['HR'],
        responses={
            200: InsuranceFormSerializer,
            404: {'description': 'Insurance form not found'}
        }
    )
)
class InsuranceFormDetailView(generics.RetrieveAPIView):
    """جزئیات فرم بیمه"""
    serializer_class = InsuranceFormSerializer
    permission_classes = [HRPermission]

    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'sys_admin':
            return InsuranceForm.objects.all()
        
        if user.role == 'hr':
            if user.centers.exists():
                return InsuranceForm.objects.filter(
                    user__centers__in=user.centers.all()
                ).distinct()
            return InsuranceForm.objects.none()
        
        return InsuranceForm.objects.filter(user=user)


@extend_schema(
    operation_id='update_insurance_form_status',
    summary='Update Insurance Form Status',
    description='Update insurance form status and review comment (only HR and System Admin)',
    tags=['HR'],
    request=InsuranceFormUpdateSerializer,
    responses={
        200: InsuranceFormSerializer,
        400: {'description': 'Validation error'},
        403: {'description': 'Permission denied'},
        404: {'description': 'Insurance form not found'}
    }
)
@api_view(['PUT', 'PATCH'])
@permission_classes([HRUpdatePermission])
def update_insurance_form_status(request, pk):
    """تغییر وضعیت فرم بیمه"""
    try:
        insurance_form = InsuranceForm.objects.get(pk=pk)
    except InsuranceForm.DoesNotExist:
        return Response({
            'error': 'فرم بیمه یافت نشد'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # بررسی دسترسی
    user = request.user
    if user.role == 'hr':
        if not user.centers.exists() or not insurance_form.user.centers.exists():
            return Response({
                'error': 'شما دسترسی به این فرم بیمه ندارید'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # بررسی اینکه آیا حداقل یک مرکز مشترک وجود دارد
        common_centers = insurance_form.user.centers.filter(id__in=user.centers.values_list('id', flat=True))
        if not common_centers.exists():
            return Response({
                'error': 'شما دسترسی به این فرم بیمه ندارید'
            }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = InsuranceFormUpdateSerializer(
        insurance_form,
        data=request.data,
        partial=request.method == 'PATCH',
        context={'request': request}
    )
    
    if serializer.is_valid():
        serializer.save()
        response_serializer = InsuranceFormSerializer(insurance_form, context={'request': request})
        return Response(response_serializer.data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ========== PhoneBook Views ==========

@extend_schema(
    operation_id='phonebook_search',
    summary='Search PhoneBook',
    description='Search phonebook entries by title or phone number. All authenticated users can search.',
    tags=['HR'],
    parameters=[
        {
            'name': 'search',
            'in': 'query',
            'description': 'جستجو در عنوان یا شماره تلفن',
            'required': False,
            'schema': {'type': 'string'}
        }
    ],
    responses={
        200: PhoneBookSerializer(many=True),
        400: {'description': 'Validation error'}
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def phonebook_search(request):
    """جستجو در دفترچه تلفن"""
    search_query = request.query_params.get('search', '').strip()
    
    queryset = PhoneBook.objects.all()
    
    if search_query:
        # جستجو در عنوان و شماره تلفن
        queryset = queryset.filter(
            Q(title__icontains=search_query) | Q(phone__icontains=search_query)
        )
    
    serializer = PhoneBookSerializer(queryset, many=True, context={'request': request})
    return Response(serializer.data)


# ========== Story Views ==========

@extend_schema_view(
    get=extend_schema(
        operation_id='story_list',
        summary='List Stories',
        description='Get list of stories. All authenticated users (employees, admins, HR) can view active stories. HR and System Admin can see all stories (active and inactive).',
        tags=['HR']
    ),
    post=extend_schema(
        operation_id='story_create',
        summary='Create Story',
        description='Create new story. Only HR and System Admin can create stories.',
        tags=['HR'],
        request=StoryCreateSerializer,
        responses={
            201: StorySerializer,
            400: {'description': 'Validation error'},
            403: {'description': 'Permission denied. Only HR and System Admin can create stories.'}
        }
    )
)
class StoryListView(generics.ListCreateAPIView):
    """لیست و ایجاد استوری‌ها"""
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPageNumberPagination
    parser_classes = [JSONParser, MultiPartParser, FormParser]  # پشتیبانی از JSON و form-data برای آپلود فایل
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return StoryCreateSerializer
        return StoryListSerializer

    def get_queryset(self):
        user = self.request.user
        
        # ادمین سیستم و ادمین HR می‌توانند همه استوری‌ها را ببینند (فعال و غیرفعال)
        if user.role in ['sys_admin', 'hr']:
            queryset = Story.objects.all().select_related('created_by')
            
            # فیلتر بر اساس وضعیت فعال/غیرفعال (فقط برای ادمین‌ها)
            is_active_param = self.request.query_params.get('is_active')
            if is_active_param is not None:
                is_active = is_active_param.lower() in ['true', '1', 'yes']
                queryset = queryset.filter(is_active=is_active)
        else:
            # همه کاربران احراز هویت شده (کارمند، ادمین غذا و ...) می‌توانند استوری‌های فعال را ببینند
            queryset = Story.objects.filter(is_active=True).select_related('created_by')
        
        # فیلتر کردن استوری‌های منقضی شده - فقط استوری‌هایی که فایل دارند نمایش داده شوند
        queryset = queryset.filter(
            Q(expiry_date__isnull=True) | Q(expiry_date__gt=timezone.now())
        ).filter(
            # فقط استوری‌هایی که حداقل یکی از فایل‌ها را دارند
            Q(thumbnail_image__isnull=False) | Q(content_file__isnull=False)
        )
        
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        """ایجاد استوری توسط کاربر فعلی"""
        # بررسی دسترسی: فقط HR و System Admin می‌توانند استوری ایجاد کنند
        user = self.request.user
        if user.role not in ['hr', 'sys_admin']:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("فقط ادمین نیروی انسانی و ادمین سیستم می‌توانند استوری ایجاد کنند")
        
        serializer.save(created_by=user)


@extend_schema_view(
    get=extend_schema(
        operation_id='story_detail',
        summary='Get Story Details',
        description='Get story details. All authenticated users (employees, admins, HR) can view active story details. HR and System Admin can view all story details (active and inactive).',
        tags=['HR'],
        responses={
            200: StorySerializer,
            404: {'description': 'Story not found'}
        }
    ),
    put=extend_schema(
        operation_id='story_update',
        summary='Update Story',
        description='Update story. Only HR and System Admin can update stories.',
        tags=['HR'],
        request=StoryCreateSerializer,
        responses={
            200: StorySerializer,
            400: {'description': 'Validation error'},
            403: {'description': 'Permission denied. Only HR and System Admin can update stories.'},
            404: {'description': 'Story not found'}
        }
    ),
    patch=extend_schema(
        operation_id='story_partial_update',
        summary='Partial Update Story',
        description='Partially update story. Only HR and System Admin can update stories.',
        tags=['HR'],
        request=StoryCreateSerializer,
        responses={
            200: StorySerializer,
            400: {'description': 'Validation error'},
            403: {'description': 'Permission denied. Only HR and System Admin can update stories.'},
            404: {'description': 'Story not found'}
        }
    ),
    delete=extend_schema(
        operation_id='story_delete',
        summary='Delete Story',
        description='Delete story. Only HR and System Admin can delete stories.',
        tags=['HR'],
        responses={
            204: {'description': 'Story deleted successfully'},
            403: {'description': 'Permission denied. Only HR and System Admin can delete stories.'},
            404: {'description': 'Story not found'}
        }
    )
)
class StoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """جزئیات استوری"""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return StoryCreateSerializer
        return StorySerializer

    def get_queryset(self):
        user = self.request.user
        
        # ادمین سیستم و ادمین HR می‌توانند همه استوری‌ها را ببینند (فعال و غیرفعال)
        if user.role in ['sys_admin', 'hr']:
            queryset = Story.objects.all().select_related('created_by')
        else:
            # همه کاربران احراز هویت شده (کارمند، ادمین غذا و ...) می‌توانند استوری‌های فعال را ببینند
            queryset = Story.objects.filter(is_active=True).select_related('created_by')
        
        # فیلتر کردن استوری‌های منقضی شده - فقط استوری‌هایی که فایل دارند نمایش داده شوند
        queryset = queryset.filter(
            Q(expiry_date__isnull=True) | Q(expiry_date__gt=timezone.now())
        ).filter(
            # فقط استوری‌هایی که حداقل یکی از فایل‌ها را دارند
            Q(thumbnail_image__isnull=False) | Q(content_file__isnull=False)
        )
        
        return queryset
    
    def update(self, request, *args, **kwargs):
        """به‌روزرسانی استوری"""
        # بررسی دسترسی: فقط HR و System Admin می‌توانند استوری را به‌روزرسانی کنند
        user = request.user
        if user.role not in ['hr', 'sys_admin']:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("فقط ادمین نیروی انسانی و ادمین سیستم می‌توانند استوری را ویرایش کنند")
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """حذف استوری"""
        # بررسی دسترسی: فقط HR و System Admin می‌توانند استوری را حذف کنند
        user = request.user
        if user.role not in ['hr', 'sys_admin']:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("فقط ادمین نیروی انسانی و ادمین سیستم می‌توانند استوری را حذف کنند")
        
        return super().destroy(request, *args, **kwargs)


class MyAnnouncementsView(generics.ListAPIView):
    """اطلاعیه‌های شخصی کاربر فعلی"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AnnouncementListSerializer
    pagination_class = CustomPageNumberPagination
    
    def get_queryset(self):
        user = self.request.user
        user_centers = user.centers.all()
        
        return Announcement.objects.filter(
            is_active=True,
            is_announcement=True
        ).filter(
            Q(centers__in=user_centers) | Q(send_to_all_users=True) | Q(target_users=user)
        ).distinct().order_by('-publish_date')



@extend_schema_view(
    get=extend_schema(
        tags=["First Page Image"],
        summary="Get first page image",
        description="Returns the single image used for the first page (singleton resource).",
        responses={
            200: FirstPageImageSerializer,
            404: None,
        },
    )
)
class FirstPageImageView(APIView):
    permission_classes = []

    def get(self, request):
        obj = FirstPageImage.objects.first()

        if not obj:
            return Response(
                {"detail": "No image found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = FirstPageImageSerializer(obj, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)