from rest_framework import serializers
from .models import Center


class CenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Center
        fields = [
            'id', 'name', 'city', 'address', 'phone', 'email',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CenterListSerializer(serializers.ModelSerializer):
    employee_count = serializers.SerializerMethodField()

    class Meta:
        model = Center
        fields = [
            'id', 'name', 'city', 'phone', 'email',
            'is_active', 'employee_count', 'created_at'
        ]

    def get_employee_count(self, obj):
        return obj.user_set.count()


