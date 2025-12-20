# راهنمای استفاده از صفحه تست Push Notifications

## دسترسی به صفحه

بعد از اجرای سرور Django، به آدرس زیر بروید:

```
http://localhost:14532/test-notifications/
```

## مراحل استفاده

### 1. وارد کردن اطلاعات

- **API Base URL**: آدرس سرور شما (مثلاً `http://localhost:14532`)
- **Access Token**: توکن JWT خود را وارد کنید (می‌توانید از Swagger UI یا Postman دریافت کنید)
- **VAPID Public Key**: کلید عمومی VAPID که در تنظیمات پروژه تعریف کرده‌اید

### 2. دریافت مجوز

روی دکمه "🔐 درخواست مجوز Push Notification" کلیک کنید و در پنجره popup مرورگر، "Allow" را انتخاب کنید.

### 3. ثبت Subscription

بعد از دریافت مجوز، روی دکمه "✅ ثبت Subscription" کلیک کنید. این کار subscription شما را در سرور ثبت می‌کند.

### 4. تست ارسال نوتفیکیشن

حالا می‌توانید روی دکمه "📤 ارسال نوتفیکیشن تستی" کلیک کنید تا یک نوتفیکیشن تستی برای خودتان ارسال شود.

### 5. مشاهده Subscription‌ها

با کلیک روی "📋 مشاهده Subscription‌ها" می‌توانید لیست تمام subscription‌های ثبت شده خود را ببینید.

### 6. حذف Subscription

اگر می‌خواهید subscription را حذف کنید، روی دکمه "❌ حذف Subscription" کلیک کنید.

## نکات مهم

1. **HTTPS در Production**: در محیط production، Push Notifications فقط روی HTTPS کار می‌کند. در development، localhost استثناست.

2. **Service Worker**: Service Worker به صورت خودکار ثبت می‌شود. اگر خطا داد، مطمئن شوید که فایل `service-worker.js` در پوشه `static` وجود دارد.

3. **VAPID Keys**: حتماً VAPID keys را در environment variables تنظیم کنید.

4. **Access Token**: برای دریافت Access Token:
   - از Swagger UI: `/api/docs/`
   - از Postman
   - یا از endpoint login: `/api/auth/login/`

## عیب‌یابی

### مشکل: "Service Worker ثبت نشد"
- مطمئن شوید که فایل `service-worker.js` در پوشه `static` وجود دارد
- بررسی کنید که static files به درستی serve می‌شوند

### مشکل: "مجوز داده نشد"
- از تنظیمات مرورگر، مجوز Notifications را فعال کنید
- در Chrome: Settings > Privacy and security > Site settings > Notifications

### مشکل: "Subscription ثبت نشد"
- بررسی کنید که Access Token معتبر است
- مطمئن شوید که VAPID Public Key درست است
- در Console مرورگر خطاها را بررسی کنید

### مشکل: "نوتفیکیشن دریافت نمی‌شود"
- مطمئن شوید که subscription ثبت شده است
- بررسی کنید که VAPID keys درست تنظیم شده‌اند
- در Console مرورگر خطاها را بررسی کنید

## تست از Backend

همچنین می‌توانید از Django Shell استفاده کنید:

```python
python manage.py shell

from apps.accounts.models import User
from apps.notifications.services import send_push_notification

user = User.objects.first()
send_push_notification(
    user=user,
    title='تست',
    body='این یک تست است'
)
```

