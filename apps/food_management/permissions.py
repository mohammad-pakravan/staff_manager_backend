from rest_framework import permissions


class IsFoodAdminOrSystemAdmin(permissions.BasePermission):
    """دسترسی فقط برای ادمین غذا و ادمین سیستم"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.role in ['admin_food', 'sys_admin']


class IsFoodAdminSystemAdminOrEmployee(permissions.BasePermission):
    """دسترسی برای ادمین غذا، ادمین سیستم و همه کاربران احراز هویت شده"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # همه کاربران احراز هویت شده دسترسی دارند
        return True


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
    - HR Admin: فقط دسترسی به endpoint های employee (مشاهده منو، رزرو و ...)
    - همه کاربران احراز هویت شده: فقط endpoint های /employee/ و endpoint های مربوط به خودش
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        user = request.user
        path = request.path
        
        # System Admin دسترسی کامل دارد
        if user.role == 'sys_admin':
            return True
        
        # Food Admin دسترسی کامل به food endpoints دارد
        if user.role == 'admin_food':
            return True
        
        # اگر HR است، فقط به endpoint های employee و رزرو دسترسی دارد
        if user.role == 'hr':
            # بررسی endpoint های employee که HR می‌تواند به آن‌ها دسترسی داشته باشد
            if '/employee/' in path:
                return True
            # مشاهده منوهای روزانه (فقط خواندنی)
            if '/daily-menus/' in path and request.method in permissions.SAFE_METHODS:
                return True
            # مشاهده انواع وعده غذایی (فقط خواندنی)
            if '/meal-types/' in path and request.method in permissions.SAFE_METHODS:
                return True
            # مشاهده و ایجاد رزروهای خودش
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
            # مشاهده و ایجاد رزروهای مهمان خودش
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
            # رزروهای دسر
            if '/dessert-reservations/' in path:
                # GET برای مشاهده لیست رزروهای دسر خودش
                if request.method in permissions.SAFE_METHODS:
                    return True
                # POST برای ایجاد رزرو دسر
                if request.method == 'POST':
                    return True
                # POST برای لغو رزروهای دسر خودش
                if '/cancel/' in path and request.method == 'POST':
                    return True
            # رزروهای دسر مهمان
            if '/guest-dessert-reservations/' in path:
                # GET برای مشاهده لیست رزروهای دسر مهمان خودش
                if request.method in permissions.SAFE_METHODS:
                    return True
                # POST برای ایجاد رزرو دسر مهمان
                if request.method == 'POST':
                    return True
                # POST برای لغو رزروهای دسر مهمان خودش
                if '/cancel/' in path and request.method == 'POST':
                    return True
            # مشاهده رزروهای خودش
            if '/user/reservations/' in path:
                return True
            if '/user/guest-reservations/' in path:
                return True
            if '/user/guest-dessert-reservations/' in path:
                return True
            if '/user/reservations/summary/' in path and request.method in permissions.SAFE_METHODS:
                return True
            # مشاهده محدودیت‌های رزرو
            if '/reservations/limits/' in path and request.method in permissions.SAFE_METHODS:
                return True
            if '/guest-reservations/limits/' in path and request.method in permissions.SAFE_METHODS:
                return True
            if '/dessert-reservations/limits/' in path and request.method in permissions.SAFE_METHODS:
                return True
            if '/guest-dessert-reservations/limits/' in path and request.method in permissions.SAFE_METHODS:
                return True
            # HR به endpoint های مدیریتی دسترسی ندارد
            return False
        
        # همه کاربران احراز هویت شده (به جز HR که قبلاً بررسی شد) می‌توانند به endpoint های employee و endpoint های مربوط به خودش دسترسی داشته باشند
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
        # رزروهای دسر
        if '/dessert-reservations/' in path:
            # GET برای مشاهده لیست رزروهای دسر خودش
            if request.method in permissions.SAFE_METHODS:
                return True
            # POST برای ایجاد رزرو دسر
            if request.method == 'POST':
                return True
            # POST برای لغو رزروهای دسر خودش
            if '/cancel/' in path and request.method == 'POST':
                return True
        # رزروهای دسر مهمان
        if '/guest-dessert-reservations/' in path:
            # GET برای مشاهده لیست رزروهای دسر مهمان خودش
            if request.method in permissions.SAFE_METHODS:
                return True
            # POST برای ایجاد رزرو دسر مهمان
            if request.method == 'POST':
                return True
            # POST برای لغو رزروهای دسر مهمان خودش
            if '/cancel/' in path and request.method == 'POST':
                return True
        # مشاهده رزروهای دسر خودش
        if '/user/guest-dessert-reservations/' in path:
            return True
        # مشاهده محدودیت‌های رزرو دسر
        if '/dessert-reservations/limits/' in path and request.method in permissions.SAFE_METHODS:
            return True
        if '/guest-dessert-reservations/limits/' in path and request.method in permissions.SAFE_METHODS:
            return True
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


class UserReportPermission(permissions.BasePermission):
    """
    دسترسی برای endpoint های گزارش کاربر
    - System Admin: دسترسی کامل (می‌تواند گزارش همه کاربران را ببیند)
    - Food Admin: دسترسی کامل (می‌تواند گزارش همه کاربران را ببیند)
    - همه کاربران احراز هویت شده: فقط می‌توانند گزارش خودشان را ببینند
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # System Admin و Food Admin دسترسی کامل دارند
        if user.role in ['sys_admin', 'admin_food']:
            return True
        
        # همه کاربران احراز هویت شده فقط می‌توانند گزارش خودشان را ببینند
        # بررسی می‌کنیم که آیا user_id در query params وجود دارد یا نه
        # اگر وجود داشته باشد و با user لاگین شده متفاوت باشد، دسترسی رد می‌شود
        user_id_param = request.query_params.get('user_id')
        if user_id_param:
            try:
                requested_user_id = int(user_id_param)
                # اگر user_id متفاوت از user لاگین شده باشد، دسترسی رد می‌شود
                if requested_user_id != user.id:
                    return False
            except (ValueError, TypeError):
                # اگر user_id معتبر نباشد، اجازه می‌دهیم که view خودش خطا را مدیریت کند
                pass
        # اگر user_id ارسال نشده باشد، گزارش برای کاربر لاگین شده است که مجاز است
        return True

class UserHumanResourcesPermission(permissions.BasePermission):
    """دسترسی برای endpoint های Human Resources"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False    
        user = request.user
        if user.role == 'hr':
            return True
        if user.role == 'sys_admin':
            return True
        return False