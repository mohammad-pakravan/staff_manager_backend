from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from drf_spectacular.types import OpenApiTypes
from .models import Announcement
from .serializers import (
    AnnouncementSerializer, 
    AnnouncementCreateSerializer, 
    AnnouncementListSerializer
)
# from apps.core.utils import get_jalali_now  # Not needed anymore
from apps.core.pagination import CustomPageNumberPagination


@extend_schema_view(
    get=extend_schema(
        operation_id='announcement_list',
        summary='List Announcements',
        description='Get list of announcements (regular users: own center, HR: all)',
        tags=['HR']
    ),
    post=extend_schema(
        operation_id='announcement_create',
        summary='Create Announcement',
        description='Create new announcement (only for HR and System Admin)',
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
    """لیست و ایجاد اطلاعیه‌ها"""
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPageNumberPagination
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AnnouncementCreateSerializer
        return AnnouncementListSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Announcement.objects.filter(is_active=True)
        
        # ادمین سیستم و ادمین HR می‌توانند همه اطلاعیه‌ها را ببینند
        if user.role in ['sys_admin', 'hr']:
            pass  # همه اطلاعیه‌ها
        # کاربران عادی فقط اطلاعیه‌های مرکز خود را می‌بینند
        elif user.center:
            queryset = queryset.filter(center=user.center)
        else:
            queryset = queryset.none()
        
        # فیلتر بر اساس مرکز (فقط برای ادمین‌ها)
        center_id = self.request.query_params.get('center')
        if center_id and user.role in ['sys_admin', 'hr']:
            queryset = queryset.filter(center_id=center_id)
        
        return queryset.order_by('-publish_date')

    def perform_create(self, serializer):
        """ایجاد اطلاعیه توسط کاربر فعلی"""
        user = self.request.user
        # فقط HR و System Admin می‌توانند اطلاعیه ایجاد کنند
        if user.role not in ['hr', 'sys_admin']:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("فقط نیروی انسانی می‌تواند اطلاعیه ایجاد کند")
        
        # ادمین HR و System Admin می‌توانند برای هر مرکزی اطلاعیه ایجاد کنند
        serializer.save(created_by=user)


@extend_schema_view(
    get=extend_schema(
        operation_id='announcement_detail',
        summary='Get Announcement Details',
        description='Get details of a specific announcement',
        tags=['HR'],
        responses={
            200: AnnouncementSerializer,
            404: {'description': 'Announcement not found'}
        }
    ),
    put=extend_schema(
        operation_id='announcement_update',
        summary='Update Announcement',
        description='Update announcement completely (only for HR and System Admin)',
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
        summary='Partial Update Announcement',
        description='Partially update announcement (only for HR and System Admin)',
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
        summary='Delete Announcement',
        description='Delete announcement (only for HR and System Admin)',
        tags=['HR'],
        responses={
            204: {'description': 'Announcement deleted'},
            403: {'description': 'Permission denied'},
            404: {'description': 'Announcement not found'}
        }
    )
)
class AnnouncementDetailView(generics.RetrieveUpdateDestroyAPIView):
    """جزئیات، ویرایش و حذف اطلاعیه"""
    serializer_class = AnnouncementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Announcement.objects.all()
        
        # ادمین سیستم و ادمین HR می‌توانند همه اطلاعیه‌ها را ببینند
        if user.role in ['sys_admin', 'hr']:
            pass  # همه اطلاعیه‌ها
        # کاربران عادی فقط اطلاعیه‌های مرکز خود را می‌بینند
        elif user.center:
            queryset = queryset.filter(center=user.center)
        else:
            queryset = queryset.none()
        
        return queryset

    def perform_update(self, serializer):
        """ویرایش اطلاعیه"""
        user = self.request.user
        # فقط HR و System Admin می‌توانند اطلاعیه ویرایش کنند
        if user.role not in ['hr', 'sys_admin']:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("فقط نیروی انسانی می‌تواند اطلاعیه ویرایش کند")
        
        # ادمین HR و System Admin می‌توانند همه اطلاعیه‌ها را ویرایش کنند
        serializer.save()

    def perform_destroy(self, instance):
        """حذف اطلاعیه"""
        user = self.request.user
        # فقط HR و System Admin می‌توانند اطلاعیه حذف کنند
        if user.role not in ['hr', 'sys_admin']:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("فقط نیروی انسانی می‌تواند اطلاعیه حذف کند")
        
        # ادمین HR و System Admin می‌توانند همه اطلاعیه‌ها را حذف کنند
        instance.delete()


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
        'recent_announcements': Announcement.objects.filter(
            is_active=True
        ).order_by('-publish_date')[:5].values(
            'id', 'title', 'center__name', 'publish_date'
        )
    }
    
    # آمار بر اساس مرکز
    center_stats = Center.objects.annotate(
        announcement_count=Count('announcement', filter=Q(announcement__is_active=True))
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
    
    created_announcements = []
    
    # ایجاد اطلاعیه برای هر مرکز
    for center in centers:
        announcement = Announcement.objects.create(
            title=title,
            content=content,
            publish_date=publish_date,
            center=center,
            is_active=is_active,
            created_by=user
        )
        created_announcements.append({
            'id': announcement.id,
            'title': announcement.title,
            'center_name': center.name,
            'is_active': announcement.is_active
        })
    
    return Response({
        'message': f'اطلاعیه برای {len(created_announcements)} مرکز ایجاد شد',
        'announcements': created_announcements
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
def publish_announcement(request, announcement_id):
    """انتشار اطلاعیه"""
    if request.user.role not in ['hr', 'sys_admin']:
        return Response({
            'error': 'دسترسی غیرمجاز'
        }, status=status.HTTP_403_FORBIDDEN)
    
    announcement = get_object_or_404(Announcement, id=announcement_id)
    announcement.is_active = True
    announcement.publish_date = timezone.now()
    announcement.save()
    
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
def unpublish_announcement(request, announcement_id):
    """لغو انتشار اطلاعیه"""
    if request.user.role not in ['hr', 'sys_admin']:
        return Response({
            'error': 'دسترسی غیرمجاز'
        }, status=status.HTTP_403_FORBIDDEN)
    
    announcement = get_object_or_404(Announcement, id=announcement_id)
    announcement.is_active = False
    announcement.save()
    
    return Response({
        'message': 'انتشار اطلاعیه لغو شد',
        'announcement': AnnouncementSerializer(announcement).data
    })

