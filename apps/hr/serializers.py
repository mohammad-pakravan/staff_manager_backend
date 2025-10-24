from rest_framework import serializers
from .models import Announcement
from apps.centers.serializers import CenterSerializer
from apps.accounts.serializers import UserSerializer
from apps.core.utils import to_jalali_date, format_jalali_date


class AnnouncementSerializer(serializers.ModelSerializer):
    """Serializer for Announcement model"""
    center_name = serializers.CharField(source='center.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    jalali_publish_date = serializers.SerializerMethodField()
    jalali_created_at = serializers.SerializerMethodField()
    
    class Meta:
        model = Announcement
        fields = [
            'id', 'title', 'content', 'image', 'publish_date', 
            'center', 'center_name', 'created_by', 'created_by_name',
            'is_active', 'created_at', 'updated_at',
            'jalali_publish_date', 'jalali_created_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def get_jalali_publish_date(self, obj):
        """Get Jalali publish date"""
        return format_jalali_date(obj.jalali_publish_date, '%Y/%m/%d %H:%M')

    def get_jalali_created_at(self, obj):
        """Get Jalali created date"""
        return format_jalali_date(obj.jalali_created_at, '%Y/%m/%d %H:%M')

    def create(self, validated_data):
        """Create announcement with current user as creator"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class AnnouncementCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Announcement"""
    
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'image', 'publish_date', 'center', 'is_active']

    def create(self, validated_data):
        """Create announcement with current user as creator"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class AnnouncementListSerializer(serializers.ModelSerializer):
    """Serializer for listing Announcements"""
    center_name = serializers.CharField(source='center.name', read_only=True)
    jalali_publish_date = serializers.SerializerMethodField()
    
    class Meta:
        model = Announcement
        fields = [
            'id', 'title', 'content', 'image', 'publish_date',
            'center_name', 'is_active', 'jalali_publish_date'
        ]

    def get_jalali_publish_date(self, obj):
        """Get Jalali publish date"""
        return format_jalali_date(obj.jalali_publish_date, '%Y/%m/%d')


