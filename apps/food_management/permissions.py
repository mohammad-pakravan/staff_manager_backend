from rest_framework import permissions


class IsFoodAdminOrSystemAdmin(permissions.BasePermission):
    """دسترسی فقط برای ادمین غذا و ادمین سیستم"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.role in ['admin_food', 'sys_admin']


class IsFoodAdminSystemAdminOrEmployee(permissions.BasePermission):
    """دسترسی برای ادمین غذا، ادمین سیستم و کارمندان"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.role in ['admin_food', 'sys_admin', 'employee']


class IsSystemAdmin(permissions.BasePermission):
    """دسترسی فقط برای ادمین سیستم"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.role == 'sys_admin'


class FoodManagementPermission(permissions.BasePermission):
    """
    دسترسی برای Food Management endpoints
    - System Admin: دسترسی کامل به همه چیز
    - Food Admin: دسترسی کامل به food endpoints (غذا، رستوران، اپشن، منو، رزرو)
    - HR Admin: بدون دسترسی به food endpoints (فقط endpoint های HR)
    - Employee: فقط endpoint های /employee/ و endpoint های مربوط به خودش
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # System Admin دسترسی کامل دارد
        if user.role == 'sys_admin':
            return True
        
        # Food Admin دسترسی کامل به food endpoints دارد
        if user.role == 'admin_food':
            return True
        
        # HR Admin نباید به food endpoints دسترسی داشته باشد
        if user.role == 'hr':
            return False
        
        # Employee فقط endpoint های employee و endpoint های مربوط به خودش
        if user.role == 'employee':
            path = request.path
            # Employee endpoint ها
            if '/employee/' in path:
                return True
            # مشاهده و مدیریت رزروهای خودش
            if '/reservations/' in path:
                # GET برای مشاهده لیست رزروهای خودش
                if request.method in permissions.SAFE_METHODS:
                    return True
                # POST برای ایجاد رزرو
                if request.method == 'POST':
                    return True
                # POST برای لغو رزروهای خودش
                if '/cancel/' in path and request.method == 'POST':
                    return True
            # مشاهده و مدیریت رزروهای مهمان خودش
            if '/guest-reservations/' in path:
                # GET برای مشاهده لیست رزروهای مهمان خودش
                if request.method in permissions.SAFE_METHODS:
                    return True
                # POST برای ایجاد رزرو مهمان
                if request.method == 'POST':
                    return True
                # POST برای لغو رزروهای مهمان خودش
                if '/cancel/' in path and request.method == 'POST':
                    return True
            # مشاهده منوهای روزانه
            if '/daily-menus/' in path and request.method in permissions.SAFE_METHODS:
                return True
            # مشاهده انواع وعده غذایی
            if '/meal-types/' in path and request.method in permissions.SAFE_METHODS:
                return True
            # مشاهده رزروهای خودش
            if '/user/reservations/' in path:
                return True
            if '/user/guest-reservations/' in path:
                return True
            if '/user/reservations/summary/' in path and request.method in permissions.SAFE_METHODS:
                return True
            # مشاهده محدودیت‌های رزرو
            if '/reservations/limits/' in path and request.method in permissions.SAFE_METHODS:
                return True
            if '/guest-reservations/limits/' in path and request.method in permissions.SAFE_METHODS:
                return True
            # رزروهای ترکیبی (combined reservations)
            if '/combined-reservations/' in path:
                # POST برای ایجاد رزرو ترکیبی
                if request.method == 'POST':
                    return True
                # PUT/PATCH برای ویرایش رزرو ترکیبی خودش
                if '/update/' in path and request.method in ['PUT', 'PATCH']:
                    return True
                # DELETE برای حذف رزرو ترکیبی خودش
                if '/delete/' in path and request.method == 'DELETE':
                    return True
            return False
        
        return False


class StatisticsPermission(permissions.BasePermission):
    """
    دسترسی برای endpoint های آمار و گزارش
    - System Admin: دسترسی کامل
    - Food Admin: دسترسی کامل
    - HR Admin: فقط مشاهده آمار (خواندنی)
    - Employee: بدون دسترسی
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # System Admin و Food Admin دسترسی کامل دارند
        if user.role in ['sys_admin', 'admin_food']:
            return True
        
        # HR Admin فقط می‌تواند آمار را مشاهده کند (خواندنی)
        if user.role == 'hr' and request.method in permissions.SAFE_METHODS:
            return True
        
        # Employee بدون دسترسی
        return False

