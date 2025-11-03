from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User


class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    center_name = serializers.SerializerMethodField()
    center_names = serializers.SerializerMethodField()
    centers_detail = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'role_display', 'centers', 'center_name', 'center_names', 'centers_detail',
            'phone_number', 'is_active', 'date_joined', 'created_at'
        ]
        read_only_fields = ['id', 'date_joined', 'created_at']

    def get_center_name(self, obj):
        """برای backward compatibility - نام اولین مرکز"""
        center = obj.center
        return center.name if center else None

    def get_center_names(self, obj):
        """لیست نام‌های تمام مراکز"""
        return [center.name for center in obj.centers.all()]

    def get_centers_detail(self, obj):
        """جزئیات تمام مراکز"""
        from apps.centers.serializers import CenterListSerializer
        return CenterListSerializer(obj.centers.all(), many=True).data


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'password', 'password_confirm', 'role', 'centers', 'phone_number'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # برای backward compatibility - اضافه کردن فیلد center
        from apps.centers.models import Center
        self.fields['center'] = serializers.PrimaryKeyRelatedField(
            queryset=Center.objects.filter(is_active=True),
            required=False,
            allow_null=True,
            write_only=True
        )

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs

    def create(self, validated_data):
        password_confirm = validated_data.pop('password_confirm', None)
        centers_data = validated_data.pop('centers', [])
        center = validated_data.pop('center', None)
        
        # برای backward compatibility - اگر center ارسال شد، آن را به centers اضافه می‌کنیم
        centers_list = list(centers_data) if centers_data else []
        if center and center not in centers_list:
            centers_list.append(center)
        
        user = User.objects.create_user(**validated_data)
        
        # اضافه کردن مراکز
        if centers_list:
            user.centers.set(centers_list)
        
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials.')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include username and password.')


