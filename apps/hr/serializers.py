from rest_framework import serializers
from django.utils import timezone
from .models import Announcement, Feedback, InsuranceForm, PhoneBook, Story
from apps.centers.serializers import CenterSerializer
from apps.accounts.serializers import UserSerializer
# از jalali_date برای تبدیل تاریخ استفاده می‌کنیم
from drf_spectacular.utils import extend_schema_field
from jalali_date import datetime2jalali, date2jalali
from datetime import datetime


class AnnouncementSerializer(serializers.ModelSerializer):
    """Serializer for Announcement model"""
    centers_data = CenterSerializer(source='centers', many=True, read_only=True)
    centers_names = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    image_url = serializers.SerializerMethodField()
    jalali_publish_date = serializers.SerializerMethodField()
    jalali_created_at = serializers.SerializerMethodField()
    
    class Meta:
        model = Announcement
        fields = [
            'id', 'title', 'lead', 'content', 'image', 'image_url', 'publish_date', 
            'centers', 'centers_data', 'centers_names', 'created_by', 'created_by_name',
            'is_active', 'created_at', 'updated_at',
            'jalali_publish_date', 'jalali_created_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    @extend_schema_field(serializers.CharField())
    def get_image_url(self, obj):
        """URL تصویر اطلاعیه"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
    
    def get_centers_names(self, obj):
        """Get list of center names"""
        return [center.name for center in obj.centers.all()]

    def get_jalali_publish_date(self, obj):
        """Get Jalali publish date"""
        if obj.publish_date:
            return datetime2jalali(obj.publish_date).strftime('%Y/%m/%d %H:%M')
        return None

    def get_jalali_created_at(self, obj):
        """Get Jalali created date"""
        if obj.created_at:
            return datetime2jalali(obj.created_at).strftime('%Y/%m/%d %H:%M')
        return None

    def create(self, validated_data):
        """Create announcement with current user as creator"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class AnnouncementCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Announcement"""
    
    class Meta:
        model = Announcement
        fields = ['title', 'lead', 'content', 'image', 'publish_date', 'centers', 'is_active']

    def create(self, validated_data):
        """Create announcement with current user as creator"""
        centers = validated_data.pop('centers', [])
        validated_data['created_by'] = self.context['request'].user
        announcement = super().create(validated_data)
        if centers:
            announcement.centers.set(centers)
        return announcement


class AnnouncementListSerializer(serializers.ModelSerializer):
    """Serializer for listing Announcements"""
    centers_names = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    jalali_publish_date = serializers.SerializerMethodField()
    
    class Meta:
        model = Announcement
        fields = [
            'id', 'title', 'lead', 'content', 'image', 'image_url', 'publish_date',
            'centers_names', 'is_active', 'jalali_publish_date'
        ]
    
    @extend_schema_field(serializers.CharField())
    def get_image_url(self, obj):
        """URL تصویر اطلاعیه"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
    
    def get_centers_names(self, obj):
        """Get list of center names"""
        return [center.name for center in obj.centers.all()]

    def get_jalali_publish_date(self, obj):
        """Get Jalali publish date"""
        if obj.publish_date:
            return datetime2jalali(obj.publish_date).strftime('%Y/%m/%d')
        return None


# ========== Feedback Serializers ==========

class FeedbackSerializer(serializers.ModelSerializer):
    """Serializer for Feedback model"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_full_name = serializers.SerializerMethodField()
    read_by_name = serializers.SerializerMethodField()
    jalali_created_at = serializers.SerializerMethodField()
    jalali_read_at = serializers.SerializerMethodField()
    
    class Meta:
        model = Feedback
        fields = [
            'id', 'user', 'user_name', 'user_full_name', 'message', 'status',
            'read_at', 'jalali_read_at', 'read_by', 'read_by_name',
            'created_at', 'jalali_created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at', 'read_at', 'read_by']

    @extend_schema_field(serializers.CharField())
    def get_user_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip()

    @extend_schema_field(serializers.CharField())
    def get_read_by_name(self, obj):
        if obj.read_by:
            return f"{obj.read_by.first_name} {obj.read_by.last_name}".strip()
        return None

    @extend_schema_field(serializers.CharField())
    def get_jalali_created_at(self, obj):
        if obj.created_at:
            return datetime2jalali(obj.created_at).strftime('%Y/%m/%d %H:%M')
        return None

    @extend_schema_field(serializers.CharField())
    def get_jalali_read_at(self, obj):
        if obj.read_at:
            return datetime2jalali(obj.read_at).strftime('%Y/%m/%d %H:%M')
        return None


class FeedbackCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Feedback"""
    
    class Meta:
        model = Feedback
        fields = ['message']

    def create(self, validated_data):
        """Create feedback with current user"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class FeedbackUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating Feedback status (HR only)"""
    
    class Meta:
        model = Feedback
        fields = ['status']

    def update(self, instance, validated_data):
        """Update feedback status and mark as read if needed"""
        status = validated_data.get('status')
        user = self.context['request'].user
        
        if status == Feedback.Status.READ and instance.status == Feedback.Status.UNREAD:
            instance.mark_as_read(user)
        else:
            instance.status = status
            if status == Feedback.Status.READ and not instance.read_at:
                instance.read_at = timezone.now()
                instance.read_by = user
            instance.save()
        
        return instance


# ========== Insurance Form Serializers ==========

class InsuranceFormSerializer(serializers.ModelSerializer):
    """Serializer for InsuranceForm model"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_full_name = serializers.SerializerMethodField()
    reviewed_by_name = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    jalali_created_at = serializers.SerializerMethodField()
    jalali_reviewed_at = serializers.SerializerMethodField()
    
    class Meta:
        model = InsuranceForm
        fields = [
            'id', 'user', 'user_name', 'user_full_name', 'file', 'file_url',
            'description', 'status', 'reviewed_at', 'jalali_reviewed_at',
            'reviewed_by', 'reviewed_by_name', 'review_comment',
            'created_at', 'jalali_created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at', 'reviewed_at', 'reviewed_by']

    @extend_schema_field(serializers.CharField())
    def get_user_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip()

    @extend_schema_field(serializers.CharField())
    def get_reviewed_by_name(self, obj):
        if obj.reviewed_by:
            return f"{obj.reviewed_by.first_name} {obj.reviewed_by.last_name}".strip()
        return None

    @extend_schema_field(serializers.CharField())
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None

    @extend_schema_field(serializers.CharField())
    def get_jalali_created_at(self, obj):
        if obj.created_at:
            return datetime2jalali(obj.created_at).strftime('%Y/%m/%d %H:%M')
        return None

    @extend_schema_field(serializers.CharField())
    def get_jalali_reviewed_at(self, obj):
        if obj.reviewed_at:
            return datetime2jalali(obj.reviewed_at).strftime('%Y/%m/%d %H:%M')
        return None


class InsuranceFormCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating InsuranceForm"""
    
    class Meta:
        model = InsuranceForm
        fields = ['file', 'description']

    def create(self, validated_data):
        """Create insurance form with current user"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class InsuranceFormUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating InsuranceForm status (HR only)"""
    
    class Meta:
        model = InsuranceForm
        fields = ['status', 'review_comment']

    def update(self, instance, validated_data):
        """Update insurance form status"""
        status = validated_data.get('status')
        comment = validated_data.get('review_comment', '')
        user = self.context['request'].user
        
        instance.review(user, status, comment)
        return instance


# ========== PhoneBook Serializers ==========

class PhoneBookSerializer(serializers.ModelSerializer):
    """Serializer for PhoneBook model"""
    jalali_created_at = serializers.SerializerMethodField()
    
    class Meta:
        model = PhoneBook
        fields = [
            'id', 'title', 'phone', 'created_at', 'jalali_created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    @extend_schema_field(serializers.CharField())
    def get_jalali_created_at(self, obj):
        if obj.created_at:
            return datetime2jalali(obj.created_at).strftime('%Y/%m/%d %H:%M')
        return None


# ========== Story Serializers ==========

class StorySerializer(serializers.ModelSerializer):
    """Serializer for Story model"""
  
   
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    thumbnail_image_url = serializers.SerializerMethodField()
    content_file_url = serializers.SerializerMethodField()
    content_type = serializers.SerializerMethodField()
    jalali_created_at = serializers.SerializerMethodField()
    
    class Meta:
        model = Story
        fields = [
            'id', 'text', 'thumbnail_image', 'thumbnail_image_url', 
            'content_file', 'content_file_url', 'content_type',
      
            'created_by', 'created_by_name', 'is_active', 
            'created_at', 'updated_at', 'jalali_created_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    @extend_schema_field(serializers.CharField())
    def get_thumbnail_image_url(self, obj):
        """URL تصویر شاخص"""
        if obj.thumbnail_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.thumbnail_image.url)
            return obj.thumbnail_image.url
        return None
    
    @extend_schema_field(serializers.CharField())
    def get_content_file_url(self, obj):
        """URL محتوای قابل نمایش"""
        if obj.content_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.content_file.url)
            return obj.content_file.url
        return None
    
    @extend_schema_field(serializers.CharField())
    def get_content_type(self, obj):
        """نوع محتوا (image یا video)"""
        return obj.content_type
    
 

    @extend_schema_field(serializers.CharField())
    def get_jalali_created_at(self, obj):
        """Get Jalali created date"""
        if obj.created_at:
            return datetime2jalali(obj.created_at).strftime('%Y/%m/%d %H:%M')
        return None

    def create(self, validated_data):
        """Create story with current user as creator"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class StoryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Story"""
    
    class Meta:
        model = Story
        fields = ['text', 'thumbnail_image', 'content_file', 'is_active']

    def create(self, validated_data):
        """Create story with current user as creator"""
        
        validated_data['created_by'] = self.context['request'].user
        story = super().create(validated_data)

        return story


class StoryListSerializer(serializers.ModelSerializer):
    """Serializer for listing Stories"""
 
    profile_image_url = serializers.SerializerMethodField()
    content_file_url = serializers.SerializerMethodField()
    content_type = serializers.SerializerMethodField()
    jalali_created_at = serializers.SerializerMethodField()
    
    class Meta:
        model = Story
        fields = [
            'id', 'text', 'profile_image_url',
            'content_file_url', 'content_type',
              'is_active', 'jalali_created_at'
        ]
    
    @extend_schema_field(serializers.CharField())
    def get_profile_image_url(self, obj):
        """URL تصویر پروفایل کاربر ایجادکننده"""
        if obj.created_by and obj.created_by.profile_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.created_by.profile_image.url)
            return obj.created_by.profile_image.url
        return None
    
    @extend_schema_field(serializers.CharField())
    def get_content_file_url(self, obj):
        """URL محتوای قابل نمایش"""
        if obj.content_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.content_file.url)
            return obj.content_file.url
        return None
    
    @extend_schema_field(serializers.CharField())
    def get_content_type(self, obj):
        """نوع محتوا (image یا video)"""
        return obj.content_type
    
 

    @extend_schema_field(serializers.CharField())
    def get_jalali_created_at(self, obj):
        """Get Jalali created date"""
        if obj.created_at:
            return datetime2jalali(obj.created_at).strftime('%Y/%m/%d %H:%M')
        return None
