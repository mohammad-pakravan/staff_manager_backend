"""
کلاس احراز هویت سفارشی برای JWT با پشتیبانی از HttpOnly cookies
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from rest_framework_simplejwt.tokens import UntypedToken
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class CookieJWTAuthentication(JWTAuthentication):
    """
    احراز هویت JWT که از HttpOnly cookies پشتیبانی می‌کند.
    ابتدا از cookie می‌خواند، اگر پیدا نکرد از header می‌خواند.
    """
    
    def authenticate(self, request):
        """
        تلاش برای دریافت token از cookie یا header
        """
        # ابتدا از cookie می‌خوانیم
        raw_token = request.COOKIES.get('access_token')
        
        # اگر در cookie نبود، از header می‌خوانیم (برای سازگاری با API clients)
        if not raw_token:
            header = self.get_header(request)
            if header is not None:
                raw_token = self.get_raw_token(header)
        
        if raw_token is None:
            return None
        
        try:
            # اعتبارسنجی token
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)
            
            return (user, validated_token)
        except (InvalidToken, AuthenticationFailed, Exception):
            # اگر token نامعتبر است، None برگردان (به جای exception)
            # این باعث می‌شود که endpoint های AllowAny کار کنند
            return None
    
    def get_raw_token(self, header):
        """
        استخراج token از header string
        """
        try:
            if isinstance(header, bytes):
                header = header.decode('utf-8')
            
            parts = header.split()
            
            if len(parts) == 0:
                return None
            
            if parts[0] not in ['Bearer', 'Token']:
                return None
            
            if len(parts) != 2:
                return None  # به جای exception، None برگردان
            
            return parts[1]
        except Exception:
            return None

