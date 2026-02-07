from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from drf_spectacular.utils import extend_schema_field
from ..centers.models import Center
from .models import Gathering, User


class UserSerializer(serializers.ModelSerializer):
    """سریالایزر کاربر - خروجی مرتب و ساده"""
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    centers = serializers.SerializerMethodField(read_only=True)
    position_name = serializers.SerializerMethodField(read_only=True)
    manager_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'employee_number', 'role', 'role_display', 'position', 'position_name',
            'manager', 'manager_name', 'centers',
            'phone_number', 'national_id', 'profile_image', 'max_reservations_per_day', 'max_guest_reservations_per_day',
            'is_active', 'date_joined', 'created_at'
        ]
        read_only_fields = ['id', 'date_joined', 'created_at']
    
    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_centers(self, obj):
        """برگرداندن لیست جزئیات مراکز"""
        from apps.centers.serializers import CenterListSerializer
        centers = obj.centers.all()
        if centers.exists():
            return CenterListSerializer(centers, many=True).data
        return []
    
    @extend_schema_field(serializers.CharField())
    def get_position_name(self, obj):
        """برگرداندن نام سمت"""
        if obj.position:
            return obj.position.name
        return None
    
    @extend_schema_field(serializers.CharField())
    def get_manager_name(self, obj):
        """برگرداندن نام کامل مدیر"""
        if obj.manager:
            return f"{obj.manager.first_name} {obj.manager.last_name}".strip() or obj.manager.username
        return None


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'employee_number',
            'password', 'password_confirm', 'role', 'position', 'manager', 'centers', 'phone_number',
            'national_id', 'profile_image', 'max_reservations_per_day', 'max_guest_reservations_per_day', 'is_active'
        ]
        extra_kwargs = {
            'employee_number': {'required': True},
            'phone_number': {'required': True},
            'national_id': {'required': False},
            'max_reservations_per_day': {'required': False},
            'max_guest_reservations_per_day': {'required': False},
            'is_active': {'required': False},
            'position': {'required': False},
            'manager': {'required': False},
        }

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
        
        # بررسی اینکه فقط یک مرکز ارسال شده باشد
        centers_data = attrs.get('centers', [])
        center = attrs.get('center', None)
        
        # برای backward compatibility - اگر center ارسال شد، آن را به centers اضافه می‌کنیم
        centers_list = list(centers_data) if centers_data else []
        if center and center not in centers_list:
            centers_list.append(center)
        
        # فقط یک مرکز مجاز است
        if len(centers_list) > 1:
            raise serializers.ValidationError({
                'centers': 'هر کاربر فقط می‌تواند یک مرکز داشته باشد. لطفاً فقط یک مرکز انتخاب کنید.'
            })
        
        return attrs

    def create(self, validated_data):
        password_confirm = validated_data.pop('password_confirm', None)
        centers_data = validated_data.pop('centers', [])
        center = validated_data.pop('center', None)
        
        # برای backward compatibility - اگر center ارسال شد، آن را به centers اضافه می‌کنیم
        centers_list = list(centers_data) if centers_data else []
        if center and center not in centers_list:
            centers_list.append(center)
        
        # فقط یک مرکز را نگه می‌داریم
        if len(centers_list) > 1:
            centers_list = [centers_list[0]]
        
        user = User.objects.create_user(**validated_data)
        
        # اضافه کردن مرکز (فقط یکی)
        if centers_list:
            user.centers.set(centers_list[:1])
        
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


class LoginResponseSerializer(serializers.ModelSerializer):
    """Serializer ساده برای پاسخ لاگین - فقط فیلدهای ضروری"""
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'role_display', 'phone_number', 'profile_image'
        ]
        read_only_fields = ['id']



class GatheringSerializer(serializers.ModelSerializer):
    # For read operations (GET)
    user = serializers.StringRelatedField(read_only=True)
    center = serializers.StringRelatedField(read_only=True)
    
    # For write operations (POST, PUT, PATCH)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        write_only=True,
        source='user'
    )
    center_id = serializers.PrimaryKeyRelatedField(
        queryset=Center.objects.all(),
        write_only=True,
        source='center'
    )
    
    class Meta:
        model = Gathering
        fields = [
            'id',
            'user', 'user_id',
            'name', 'last_name',
            'personal_code',
            'center', 'center_id',
            'family_members_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_personal_code(self, value):
        """Validate national code (کد ملی)"""
        # Add your validation logic for Iranian national code
        if len(value) != 10:
            raise serializers.ValidationError("کد ملی باید ۱۰ رقمی باشد.")
        # Add more validation as needed
        return value
    
    def validate_family_members_count(self, value):
        """Validate family members count"""
        if value < 1:
            raise serializers.ValidationError("تعداد اعضای خانواده باید حداقل ۱ باشد.")
        if value > 20:  # Adjust maximum as needed
            raise serializers.ValidationError("تعداد اعضای خانواده نباید از ۲۰ بیشتر باشد.")
        return value
    
    def create(self, validated_data):
        """Override create to add any custom logic"""
        # You can add additional logic here before creation
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Override update to add any custom logic"""
        # You can add additional logic here before update
        return super().update(instance, validated_data)