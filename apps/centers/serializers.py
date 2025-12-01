from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Center


class CenterSerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Center
        fields = [
            'id', 'name', 'english_name', 'logo', 'logo_url', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    @extend_schema_field(serializers.CharField())
    def get_logo_url(self, obj):
        """URL لوگو مرکز"""
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None


class CenterListSerializer(serializers.ModelSerializer):
    employee_count = serializers.SerializerMethodField()

    class Meta:
        model = Center
        fields = [
            'id', 'name', 'english_name', 'logo', 'is_active', 'employee_count', 'created_at'
        ]

    def get_employee_count(self, obj):
        return obj.users.count()


