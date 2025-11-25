"""
Permissions for HR app
"""
from rest_framework import permissions


class HRPermission(permissions.BasePermission):
    """
    دسترسی برای HR endpoints (نظرات و فرم بیمه)
    - System Admin: دسترسی کامل
    - HR: می‌تواند نظرات/فرم‌های کاربران مراکز خود را ببیند و وضعیت را تغییر دهد
    - Employee: فقط می‌تواند نظرات/فرم‌های خود را ببیند و ایجاد کند
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # System Admin دسترسی کامل دارد
        if user.role == 'sys_admin':
            return True
        
        # HR می‌تواند به همه endpoint ها دسترسی داشته باشد
        if user.role == 'hr':
            return True
        
        # Employee می‌تواند نظرات/فرم‌های خود را ببیند و ایجاد کند
        if user.role == 'employee':
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """بررسی دسترسی به object خاص"""
        user = request.user
        
        # System Admin دسترسی کامل دارد
        if user.role == 'sys_admin':
            return True
        
        # HR می‌تواند به نظرات/فرم‌های کاربران مراکز خود دسترسی داشته باشد
        if user.role == 'hr':
            # بررسی اینکه آیا کاربر object متعلق به یکی از مراکز HR است
            if hasattr(obj, 'user'):
                # برای Feedback و InsuranceForm
                obj_user = obj.user
                if obj_user.centers.exists() and user.centers.exists():
                    # بررسی اینکه آیا حداقل یک مرکز مشترک وجود دارد
                    common_centers = obj_user.centers.filter(id__in=user.centers.values_list('id', flat=True))
                    return common_centers.exists()
            return False
        
        # Employee فقط می‌تواند به نظرات/فرم‌های خود دسترسی داشته باشد
        if user.role == 'employee':
            if hasattr(obj, 'user'):
                return obj.user == user
            return False
        
        return False


class HRUpdatePermission(permissions.BasePermission):
    """
    دسترسی برای تغییر وضعیت نظرات و فرم‌های بیمه
    - فقط HR و System Admin می‌توانند وضعیت را تغییر دهند
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # فقط HR و System Admin می‌توانند وضعیت را تغییر دهند
        if user.role in ['hr', 'sys_admin']:
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """بررسی دسترسی به object خاص"""
        user = request.user
        
        # System Admin دسترسی کامل دارد
        if user.role == 'sys_admin':
            return True
        
        # HR می‌تواند وضعیت را تغییر دهد اگر کاربر object متعلق به یکی از مراکز HR باشد
        if user.role == 'hr':
            if hasattr(obj, 'user'):
                obj_user = obj.user
                if obj_user.centers.exists() and user.centers.exists():
                    common_centers = obj_user.centers.filter(id__in=user.centers.values_list('id', flat=True))
                    return common_centers.exists()
            return False
        
        return False

