"""
Serializers for notifications app
"""
from rest_framework import serializers
from .models import PushSubscription


class PushSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for PushSubscription"""
    
    class Meta:
        model = PushSubscription
        fields = ['id', 'endpoint', 'keys', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_keys(self, value):
        """بررسی وجود کلیدهای لازم"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("keys باید یک dictionary باشد")
        
        required_keys = ['p256dh', 'auth']
        for key in required_keys:
            if key not in value:
                raise serializers.ValidationError(f"کلید {key} الزامی است")
        
        return value


class PushSubscriptionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating PushSubscription"""
    
    class Meta:
        model = PushSubscription
        fields = ['endpoint', 'keys']

    def validate_keys(self, value):
        """بررسی وجود کلیدهای لازم"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("keys باید یک dictionary باشد")
        
        required_keys = ['p256dh', 'auth']
        for key in required_keys:
            if key not in value:
                raise serializers.ValidationError(f"کلید {key} الزامی است")
        
        return value

    def create(self, validated_data):
        """ایجاد subscription با کاربر فعلی"""
        validated_data['user'] = self.context['request'].user
        subscription, created = PushSubscription.objects.get_or_create(
            user=validated_data['user'],
            endpoint=validated_data['endpoint'],
            defaults={'keys': validated_data['keys']}
        )
        if not created:
            # اگر subscription وجود داشت، keys را به‌روزرسانی کن
            subscription.keys = validated_data['keys']
            subscription.save()
        return subscription


