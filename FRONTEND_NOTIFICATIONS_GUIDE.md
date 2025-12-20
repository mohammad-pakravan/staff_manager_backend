# راهنمای پیاده‌سازی Push Notifications در Frontend

این راهنما نحوه پیاده‌سازی Push Notifications را برای Frontend Developer توضیح می‌دهد.

## 📋 فهرست مطالب

1. [فلو کلی کار (Flow)](#فلو-کلی-کار-flow)
2. [پیش‌نیازها](#پیشنیازها)
3. [مراحل پیاده‌سازی](#مراحل-پیادهسازی)
4. [کدهای نمونه](#کدهای-نمونه)
5. [مدیریت خطاها](#مدیریت-خطاها)
6. [Best Practices](#best-practices)
7. [API Endpoints](#api-endpoints)

---

## فلو کلی کار (Flow)

### 📊 دیاگرام فلو

```
┌─────────────────────────────────────────────────────────────────┐
│                    کاربر وارد اپلیکیشن می‌شود                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. بررسی پشتیبانی مرورگر                                        │
│     - Service Worker پشتیبانی می‌شود؟                            │
│     - Push Notifications پشتیبانی می‌شود؟                        │
│     - Notification API پشتیبانی می‌شود؟                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ✅ پشتیبانی می‌شود
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. درخواست مجوز از کاربر                                         │
│     Notification.requestPermission()                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ✅ مجوز داده شد
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. ثبت Service Worker                                           │
│     navigator.serviceWorker.register('/service-worker.js')       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ✅ Service Worker ثبت شد
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. دریافت VAPID Public Key از سرور                              │
│     GET /api/notifications/vapid-key/                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ✅ VAPID Key دریافت شد
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. تبدیل VAPID Key                                              │
│     URL-safe Base64 → Uint8Array (64 → 65 بایت)                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ✅ Key تبدیل شد
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  6. Subscribe به Push Notifications                              │
│     registration.pushManager.subscribe({                         │
│       userVisibleOnly: true,                                     │
│       applicationServerKey: ...                                 │
│     })                                                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ✅ Subscription ایجاد شد
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  7. ارسال Subscription به سرور                                   │
│     POST /api/notifications/subscribe/                           │
│     Body: { subscription: {...} }                                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ✅ در دیتابیس ذخیره شد
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ✅ آماده دریافت نوتفیکیشن                      │
└─────────────────────────────────────────────────────────────────┘
```

### 🔄 فلو دریافت نوتفیکیشن

```
┌─────────────────────────────────────────────────────────────────┐
│              سرور نوتفیکیشن را ارسال می‌کند                      │
│         (از طریق pywebpush به Push Service)                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Push Service (FCM/Chrome)                          │
│              نوتفیکیشن را به مرورگر می‌فرستد                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Service Worker رویداد 'push' را دریافت می‌کند        │
│              self.addEventListener('push', ...)                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Service Worker داده‌ها را پردازش می‌کند               │
│              event.data.json() → { title, body, ... }            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Service Worker نوتفیکیشن را نمایش می‌دهد              │
│              self.registration.showNotification(...)            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              کاربر نوتفیکیشن را می‌بیند                          │
│              و می‌تواند روی آن کلیک کند                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    کاربر کلیک می‌کند
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Service Worker رویداد 'notificationclick' را دریافت   │
│              self.addEventListener('notificationclick', ...)     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              اپلیکیشن باز می‌شود یا focus می‌شود                   │
│              clients.openWindow(url) یا client.focus()          │
└─────────────────────────────────────────────────────────────────┘
```

### 📝 توضیح مرحله به مرحله

#### مرحله 1: راه‌اندازی اولیه (Initialization)

**زمان:** بعد از لاگین کاربر یا در صفحه اصلی

**مراحل:**
1. بررسی پشتیبانی مرورگر از Service Worker و Push Notifications
2. درخواست مجوز از کاربر برای نمایش نوتفیکیشن
3. ثبت Service Worker در مرورگر
4. بررسی اینکه آیا قبلاً subscribe شده است یا نه

**نکته:** این مراحل فقط یک بار انجام می‌شوند (یا بعد از unsubscribe)

---

#### مرحله 2: Subscribe کردن

**زمان:** وقتی کاربر دکمه "فعال کردن نوتفیکیشن" را می‌زند

**مراحل:**
1. دریافت VAPID Public Key از سرور
2. تبدیل Key از URL-safe Base64 به Uint8Array
3. اضافه کردن prefix 0x04 (تبدیل 64 بایت به 65 بایت)
4. فراخوانی `pushManager.subscribe()` با VAPID Key
5. دریافت Subscription object از مرورگر
6. ارسال Subscription به سرور برای ذخیره در دیتابیس

**Subscription Object شامل:**
```javascript
{
    endpoint: "https://fcm.googleapis.com/fcm/send/...", // آدرس Push Service
    keys: {
        p256dh: "...", // کلید رمزنگاری عمومی
        auth: "..."    // کلید احراز هویت
    }
}
```

---

#### مرحله 3: دریافت نوتفیکیشن

**زمان:** وقتی سرور نوتفیکیشن ارسال می‌کند

**مراحل:**
1. سرور از `pywebpush` استفاده می‌کند و نوتفیکیشن را به Push Service (FCM) می‌فرستد
2. Push Service نوتفیکیشن را به مرورگر کاربر می‌فرستد
3. Service Worker رویداد `push` را دریافت می‌کند
4. Service Worker داده‌های نوتفیکیشن را از `event.data` استخراج می‌کند
5. Service Worker با استفاده از `showNotification()` نوتفیکیشن را نمایش می‌دهد
6. کاربر نوتفیکیشن را می‌بیند

**داده‌های نوتفیکیشن:**
```javascript
{
    title: "عنوان نوتفیکیشن",
    body: "متن نوتفیکیشن",
    icon: "آدرس آیکون (اختیاری)",
    data: {
        type: "نوع نوتفیکیشن",
        url: "آدرس برای باز کردن",
        // سایر داده‌های سفارشی
    }
}
```

---

#### مرحله 4: کلیک روی نوتفیکیشن

**زمان:** وقتی کاربر روی نوتفیکیشن کلیک می‌کند

**مراحل:**
1. Service Worker رویداد `notificationclick` را دریافت می‌کند
2. Service Worker نوتفیکیشن را می‌بندد (`event.notification.close()`)
3. Service Worker بررسی می‌کند که آیا پنجره اپلیکیشن باز است یا نه
4. اگر باز است: focus می‌کند
5. اگر باز نیست: پنجره جدید باز می‌کند
6. کاربر به صفحه مربوطه هدایت می‌شود

---

#### مرحله 5: Unsubscribe کردن

**زمان:** وقتی کاربر می‌خواهد نوتفیکیشن را غیرفعال کند

**مراحل:**
1. دریافت Subscription فعلی از `pushManager.getSubscription()`
2. فراخوانی `subscription.unsubscribe()` برای حذف از مرورگر
3. ارسال درخواست به سرور برای حذف از دیتابیس
4. پاک کردن اطلاعات محلی (localStorage و غیره)

---

### 🔑 نکات مهم در فلو

#### 1. VAPID Key Conversion
```
VAPID Public Key (از سرور)
    ↓
URL-safe Base64 (64 کاراکتر)
    ↓
Base64 decode → 64 بایت
    ↓
اضافه کردن prefix 0x04
    ↓
Uint8Array (65 بایت) → برای PushManager
```

#### 2. Subscription Lifecycle
```
شروع
  ↓
Subscribe → در مرورگر و سرور ذخیره می‌شود
  ↓
دریافت نوتفیکیشن‌ها
  ↓
Unsubscribe → از مرورگر و سرور حذف می‌شود
```

#### 3. Service Worker Lifecycle
```
نصب (install)
  ↓
فعال (activate)
  ↓
دریافت push events
  ↓
نمایش نوتفیکیشن
  ↓
مدیریت کلیک‌ها
```

---

### 📱 سناریوهای مختلف

#### سناریو 1: کاربر جدید
```
1. کاربر وارد می‌شود
2. دکمه "فعال کردن نوتفیکیشن" را می‌بیند
3. روی دکمه کلیک می‌کند
4. مجوز داده می‌شود
5. Subscribe انجام می‌شود
6. آماده دریافت نوتفیکیشن ✅
```

#### سناریو 2: کاربر قبلی (بازگشت)
```
1. کاربر وارد می‌شود
2. بررسی می‌شود که قبلاً subscribe شده
3. اگر subscription معتبر است → هیچ کاری لازم نیست ✅
4. اگر subscription منقضی شده → دوباره subscribe می‌شود
```

#### سناریو 3: دریافت نوتفیکیشن
```
1. سرور نوتفیکیشن ارسال می‌کند
2. Service Worker دریافت می‌کند
3. نوتفیکیشن نمایش داده می‌شود
4. کاربر می‌بیند و می‌تواند کلیک کند
```

#### سناریو 4: کلیک روی نوتفیکیشن
```
1. کاربر روی نوتفیکیشن کلیک می‌کند
2. Service Worker رویداد را دریافت می‌کند
3. اپلیکیشن باز می‌شود یا focus می‌شود
4. کاربر به صفحه مربوطه هدایت می‌شود
```

---

### ⚠️ خطاها و مدیریت آن‌ها

#### خطای 1: Service Worker ثبت نشد
```
علت: فایل service-worker.js یافت نشد یا خطا دارد
راه‌حل: 
  - بررسی مسیر فایل
  - بررسی scope
  - بررسی خطاهای console
```

#### خطای 2: VAPID Key نامعتبر
```
علت: Key به درستی تبدیل نشده
راه‌حل:
  - بررسی تابع urlBase64ToUint8Array
  - بررسی طول Key (باید 64 بایت باشد)
  - بررسی prefix 0x04
```

#### خطای 3: Subscription منقضی شد (410 Gone)
```
علت: Subscription در سرور حذف شده یا منقضی شده
راه‌حل:
  - Unsubscribe کردن
  - دوباره Subscribe کردن
```

#### خطای 4: مجوز رد شد
```
علت: کاربر مجوز را رد کرده
راه‌حل:
  - نمایش پیام به کاربر
  - راهنمایی برای فعال کردن از تنظیمات مرورگر
```

---

### 🎯 چک‌لیست پیاده‌سازی

- [ ] بررسی پشتیبانی مرورگر
- [ ] درخواست مجوز از کاربر
- [ ] ثبت Service Worker
- [ ] دریافت VAPID Public Key
- [ ] تبدیل VAPID Key (64 → 65 بایت)
- [ ] Subscribe کردن
- [ ] ارسال Subscription به سرور
- [ ] پیاده‌سازی Service Worker برای دریافت push
- [ ] پیاده‌سازی نمایش نوتفیکیشن
- [ ] پیاده‌سازی مدیریت کلیک روی نوتفیکیشن
- [ ] مدیریت خطاها
- [ ] تست کامل

---

## پیش‌نیازها

### 1. بررسی پشتیبانی مرورگر

```javascript
// بررسی پشتیبانی از Service Worker و Push Notifications
if (!('serviceWorker' in navigator)) {
    console.error('Service Worker پشتیبانی نمی‌شود');
}

if (!('PushManager' in window)) {
    console.error('Push Notifications پشتیبانی نمی‌شود');
}

if (!('Notification' in window)) {
    console.error('Notifications API پشتیبانی نمی‌شود');
}
```

### 2. درخواست مجوز از کاربر

```javascript
// درخواست مجوز نمایش نوتفیکیشن
async function requestNotificationPermission() {
    if (!('Notification' in window)) {
        console.error('Notifications API پشتیبانی نمی‌شود');
        return false;
    }

    if (Notification.permission === 'granted') {
        return true;
    }

    if (Notification.permission === 'denied') {
        console.warn('کاربر مجوز نوتفیکیشن را رد کرده است');
        return false;
    }

    // درخواست مجوز
    const permission = await Notification.requestPermission();
    return permission === 'granted';
}
```

---

## مراحل پیاده‌سازی

### مرحله 1: ثبت Service Worker

```javascript
// ثبت Service Worker
async function registerServiceWorker() {
    try {
        const registration = await navigator.serviceWorker.register('/service-worker.js', {
            scope: '/' // scope باید در root باشد
        });
        
        console.log('Service Worker ثبت شد:', registration.scope);
        return registration;
    } catch (error) {
        console.error('خطا در ثبت Service Worker:', error);
        throw error;
    }
}
```

**نکته مهم:** فایل `service-worker.js` باید در root directory پروژه قرار گیرد (مثلاً `public/service-worker.js`).

### مرحله 2: دریافت VAPID Public Key

```javascript
// دریافت VAPID Public Key از سرور
async function getVapidPublicKey() {
    try {
        const response = await fetch('/api/notifications/vapid-key/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include' // برای ارسال cookies
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data.public_key;
    } catch (error) {
        console.error('خطا در دریافت VAPID Key:', error);
        throw error;
    }
}

// تبدیل VAPID Key از URL-safe base64 به Uint8Array
function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
        .replace(/\-/g, '+')
        .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }

    // VAPID Public Key باید 64 بایت باشد (بدون prefix 0x04)
    // اما برای PushManager باید 65 بایت باشد (با prefix 0x04)
    if (outputArray.length === 64) {
        // اضافه کردن prefix 0x04
        const result = new Uint8Array(65);
        result[0] = 0x04;
        result.set(outputArray, 1);
        return result;
    }

    return outputArray;
}
```

### مرحله 3: Subscribe کردن به Push Notifications

```javascript
// Subscribe کردن به Push Notifications
async function subscribeToPushNotifications(registration) {
    try {
        // دریافت VAPID Public Key
        const vapidPublicKey = await getVapidPublicKey();
        const applicationServerKey = urlBase64ToUint8Array(vapidPublicKey);

        // Subscribe کردن
        const subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true, // همیشه true باشد
            applicationServerKey: applicationServerKey
        });

        console.log('Subscription ایجاد شد:', subscription);

        // ارسال subscription به سرور
        await sendSubscriptionToServer(subscription);

        return subscription;
    } catch (error) {
        console.error('خطا در subscribe:', error);
        throw error;
    }
}

// ارسال subscription به سرور
async function sendSubscriptionToServer(subscription) {
    try {
        const response = await fetch('/api/notifications/subscribe/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include', // برای ارسال cookies
            body: JSON.stringify({
                subscription: subscription.toJSON()
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('Subscription در سرور ثبت شد:', data);
        return data;
    } catch (error) {
        console.error('خطا در ارسال subscription به سرور:', error);
        throw error;
    }
}
```

### مرحله 4: Unsubscribe کردن

```javascript
// Unsubscribe کردن از Push Notifications
async function unsubscribeFromPushNotifications(registration) {
    try {
        const subscription = await registration.pushManager.getSubscription();
        
        if (!subscription) {
            console.log('Subscription موجود نیست');
            return;
        }

        // حذف از مرورگر
        const unsubscribed = await subscription.unsubscribe();
        
        if (unsubscribed) {
            // حذف از سرور
            await removeSubscriptionFromServer(subscription);
            console.log('Unsubscribe موفق بود');
        }
    } catch (error) {
        console.error('خطا در unsubscribe:', error);
        throw error;
    }
}

// حذف subscription از سرور
async function removeSubscriptionFromServer(subscription) {
    try {
        const response = await fetch('/api/notifications/unsubscribe/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({
                subscription: subscription.toJSON()
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('Subscription از سرور حذف شد:', data);
        return data;
    } catch (error) {
        console.error('خطا در حذف subscription از سرور:', error);
        throw error;
    }
}
```

### مرحله 5: بررسی وضعیت Subscription

```javascript
// بررسی وضعیت فعلی subscription
async function checkSubscriptionStatus(registration) {
    try {
        const subscription = await registration.pushManager.getSubscription();
        
        if (subscription) {
            console.log('Subscription فعال است:', subscription.endpoint);
            return {
                subscribed: true,
                subscription: subscription
            };
        } else {
            console.log('Subscription فعال نیست');
            return {
                subscribed: false,
                subscription: null
            };
        }
    } catch (error) {
        console.error('خطا در بررسی subscription:', error);
        throw error;
    }
}
```

---

## کدهای نمونه

### مثال کامل: کلاس مدیریت نوتفیکیشن

```javascript
class NotificationManager {
    constructor() {
        this.registration = null;
        this.subscription = null;
    }

    // مقداردهی اولیه
    async init() {
        try {
            // 1. درخواست مجوز
            const hasPermission = await this.requestPermission();
            if (!hasPermission) {
                throw new Error('مجوز نوتفیکیشن داده نشد');
            }

            // 2. ثبت Service Worker
            this.registration = await this.registerServiceWorker();
            
            // 3. بررسی subscription موجود
            const status = await this.checkSubscriptionStatus();
            
            if (!status.subscribed) {
                // 4. Subscribe کردن
                await this.subscribe();
            } else {
                this.subscription = status.subscription;
                console.log('Subscription از قبل فعال است');
            }

            return true;
        } catch (error) {
            console.error('خطا در مقداردهی اولیه:', error);
            throw error;
        }
    }

    async requestPermission() {
        if (!('Notification' in window)) {
            return false;
        }

        if (Notification.permission === 'granted') {
            return true;
        }

        if (Notification.permission === 'denied') {
            return false;
        }

        const permission = await Notification.requestPermission();
        return permission === 'granted';
    }

    async registerServiceWorker() {
        const registration = await navigator.serviceWorker.register('/service-worker.js', {
            scope: '/'
        });
        return registration;
    }

    async getVapidPublicKey() {
        const response = await fetch('/api/notifications/vapid-key/', {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data.public_key;
    }

    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/\-/g, '+')
            .replace(/_/g, '/');

        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);

        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }

        if (outputArray.length === 64) {
            const result = new Uint8Array(65);
            result[0] = 0x04;
            result.set(outputArray, 1);
            return result;
        }

        return outputArray;
    }

    async subscribe() {
        const vapidPublicKey = await this.getVapidPublicKey();
        const applicationServerKey = this.urlBase64ToUint8Array(vapidPublicKey);

        this.subscription = await this.registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: applicationServerKey
        });

        await this.sendSubscriptionToServer(this.subscription);
        return this.subscription;
    }

    async sendSubscriptionToServer(subscription) {
        const response = await fetch('/api/notifications/subscribe/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({
                subscription: subscription.toJSON()
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    async unsubscribe() {
        if (!this.subscription) {
            const subscription = await this.registration.pushManager.getSubscription();
            if (!subscription) return;
            this.subscription = subscription;
        }

        const unsubscribed = await this.subscription.unsubscribe();
        
        if (unsubscribed) {
            await this.removeSubscriptionFromServer(this.subscription);
            this.subscription = null;
        }
    }

    async removeSubscriptionFromServer(subscription) {
        const response = await fetch('/api/notifications/unsubscribe/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({
                subscription: subscription.toJSON()
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    async checkSubscriptionStatus() {
        const subscription = await this.registration.pushManager.getSubscription();
        
        return {
            subscribed: !!subscription,
            subscription: subscription
        };
    }
}

// استفاده
const notificationManager = new NotificationManager();

// در زمان مناسب (مثلاً بعد از لاگین)
notificationManager.init()
    .then(() => {
        console.log('نوتفیکیشن آماده است');
    })
    .catch((error) => {
        console.error('خطا در راه‌اندازی نوتفیکیشن:', error);
    });
```

### مثال: Service Worker

```javascript
// public/service-worker.js

// نصب Service Worker
self.addEventListener('install', (event) => {
    console.log('Service Worker نصب شد');
    self.skipWaiting(); // فعال شدن فوری
});

// فعال شدن Service Worker
self.addEventListener('activate', (event) => {
    console.log('Service Worker فعال شد');
    event.waitUntil(self.clients.claim()); // کنترل فوری
});

// دریافت Push Notification
self.addEventListener('push', async (event) => {
    console.log('Push Notification دریافت شد:', event);

    let notificationData = {
        title: 'نوتفیکیشن',
        body: 'یک نوتفیکیشن جدید دریافت شد',
        icon: null,
        badge: null,
        data: {},
        tag: 'notification',
        requireInteraction: false
    };

    // پردازش داده‌های push
    if (event.data) {
        try {
            const pushData = await event.data.json();
            console.log('داده‌های push:', pushData);

            notificationData = {
                title: pushData.title || notificationData.title,
                body: pushData.body || notificationData.body,
                icon: pushData.icon || notificationData.icon,
                badge: pushData.badge || notificationData.badge,
                data: pushData.data || notificationData.data,
                tag: pushData.tag || notificationData.tag,
                requireInteraction: pushData.requireInteraction || false
            };
        } catch (error) {
            console.error('خطا در پردازش داده‌های push:', error);
            // استفاده از داده‌های پیش‌فرض
        }
    }

    // نمایش نوتفیکیشن
    const options = {
        body: notificationData.body,
        icon: notificationData.icon,
        badge: notificationData.badge,
        data: notificationData.data,
        tag: notificationData.tag,
        vibrate: [200, 100, 200],
        requireInteraction: notificationData.requireInteraction
    };

    event.waitUntil(
        self.registration.showNotification(notificationData.title, options)
    );
});

// کلیک روی نوتفیکیشن
self.addEventListener('notificationclick', (event) => {
    console.log('کلیک روی نوتفیکیشن:', event);

    event.notification.close();

    const data = event.notification.data || {};
    const url = data.url || '/';

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then((clientList) => {
                // اگر پنجره باز است، focus کن
                for (let i = 0; i < clientList.length; i++) {
                    const client = clientList[i];
                    if (client.url === url && 'focus' in client) {
                        return client.focus();
                    }
                }
                // اگر پنجره باز نیست، باز کن
                if (clients.openWindow) {
                    return clients.openWindow(url);
                }
            })
    );
});
```

---

## مدیریت خطاها

### خطاهای رایج و راه‌حل‌ها

```javascript
// 1. خطای Service Worker registration failed
try {
    const registration = await navigator.serviceWorker.register('/service-worker.js');
} catch (error) {
    if (error.message.includes('404')) {
        console.error('فایل service-worker.js یافت نشد');
    } else if (error.message.includes('scope')) {
        console.error('مشکل در scope Service Worker');
    } else {
        console.error('خطای نامشخص:', error);
    }
}

// 2. خطای Invalid applicationServerKey
try {
    const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: applicationServerKey
    });
} catch (error) {
    if (error.message.includes('applicationServerKey')) {
        console.error('VAPID Key نامعتبر است');
        // دوباره دریافت VAPID Key از سرور
        const newKey = await getVapidPublicKey();
        applicationServerKey = urlBase64ToUint8Array(newKey);
    }
}

// 3. خطای Permission denied
if (Notification.permission === 'denied') {
    console.warn('کاربر مجوز نوتفیکیشن را رد کرده است');
    // نمایش پیام به کاربر برای فعال کردن از تنظیمات مرورگر
    alert('لطفاً مجوز نوتفیکیشن را از تنظیمات مرورگر فعال کنید');
}

// 4. خطای 410 Gone (Subscription expired)
async function handleSubscriptionError(error) {
    if (error.status === 410 || error.message.includes('410')) {
        console.warn('Subscription منقضی شده است، دوباره subscribe می‌کنیم');
        // Unsubscribe و دوباره subscribe
        await notificationManager.unsubscribe();
        await notificationManager.subscribe();
    }
}
```

---

## Best Practices

### 1. بررسی وضعیت قبل از Subscribe

```javascript
// همیشه قبل از subscribe، وضعیت فعلی را بررسی کنید
async function smartSubscribe() {
    const registration = await registerServiceWorker();
    const status = await checkSubscriptionStatus(registration);
    
    if (!status.subscribed) {
        await subscribeToPushNotifications(registration);
    } else {
        console.log('از قبل subscribe شده است');
    }
}
```

### 2. مدیریت State

```javascript
// ذخیره وضعیت subscription در localStorage
function saveSubscriptionState(subscription) {
    if (subscription) {
        localStorage.setItem('push_subscription', JSON.stringify(subscription.toJSON()));
    } else {
        localStorage.removeItem('push_subscription');
    }
}

function getSubscriptionState() {
    const stored = localStorage.getItem('push_subscription');
    return stored ? JSON.parse(stored) : null;
}
```

### 3. Re-subscribe در صورت نیاز

```javascript
// بررسی و re-subscribe در صورت نیاز
async function ensureSubscription() {
    const registration = await registerServiceWorker();
    const subscription = await registration.pushManager.getSubscription();
    
    if (!subscription) {
        // اگر subscription وجود ندارد، subscribe کن
        await subscribeToPushNotifications(registration);
    } else {
        // بررسی معتبر بودن subscription در سرور
        const isValid = await checkSubscriptionValidity(subscription);
        if (!isValid) {
            // اگر معتبر نیست، دوباره subscribe کن
            await subscription.unsubscribe();
            await subscribeToPushNotifications(registration);
        }
    }
}
```

### 4. نمایش پیام‌های مناسب به کاربر

```javascript
function showNotificationStatus(status) {
    const messages = {
        'granted': 'نوتفیکیشن فعال است ✅',
        'denied': 'نوتفیکیشن غیرفعال است. لطفاً از تنظیمات مرورگر فعال کنید.',
        'default': 'لطفاً مجوز نوتفیکیشن را فعال کنید'
    };
    
    return messages[status] || messages['default'];
}
```

---

## API Endpoints

### 1. دریافت VAPID Public Key

```http
GET /api/notifications/vapid-key/
```

**Response:**
```json
{
    "public_key": "BASE64_URL_SAFE_KEY"
}
```

### 2. Subscribe

```http
POST /api/notifications/subscribe/
Content-Type: application/json
Cookie: sessionid=...

{
    "subscription": {
        "endpoint": "https://fcm.googleapis.com/...",
        "keys": {
            "p256dh": "...",
            "auth": "..."
        }
    }
}
```

**Response:**
```json
{
    "message": "Subscription ثبت شد",
    "subscription_id": 123
}
```

### 3. Unsubscribe

```http
POST /api/notifications/unsubscribe/
Content-Type: application/json
Cookie: sessionid=...

{
    "subscription": {
        "endpoint": "https://fcm.googleapis.com/...",
        "keys": {
            "p256dh": "...",
            "auth": "..."
        }
    }
}
```

**Response:**
```json
{
    "message": "Subscription حذف شد"
}
```

### 4. تست نوتفیکیشن

```http
POST /api/notifications/test/
Content-Type: application/json
Cookie: sessionid=...

{
    "title": "تست",
    "body": "این یک نوتفیکیشن تستی است"
}
```

---

## نکات مهم

1. **HTTPS ضروری است**: Push Notifications فقط در HTTPS کار می‌کنند (یا localhost برای development)

2. **Service Worker Scope**: Service Worker باید در root scope (`/`) ثبت شود

3. **Cookies**: برای ارسال subscription به سرور، باید `credentials: 'include'` استفاده شود

4. **VAPID Key**: VAPID Public Key باید از 64 بایت به 65 بایت تبدیل شود (با اضافه کردن prefix 0x04)

5. **Permission**: همیشه قبل از subscribe، مجوز کاربر را بررسی کنید

6. **Error Handling**: همیشه خطاها را مدیریت کنید و به کاربر پیام مناسب نمایش دهید

---

## مثال کامل React

```jsx
import { useState, useEffect } from 'react';

function NotificationButton() {
    const [isSubscribed, setIsSubscribed] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        checkSubscription();
    }, []);

    const checkSubscription = async () => {
        try {
            const registration = await navigator.serviceWorker.ready;
            const subscription = await registration.pushManager.getSubscription();
            setIsSubscribed(!!subscription);
        } catch (err) {
            console.error('خطا در بررسی subscription:', err);
        }
    };

    const handleSubscribe = async () => {
        setIsLoading(true);
        setError(null);

        try {
            // 1. درخواست مجوز
            const permission = await Notification.requestPermission();
            if (permission !== 'granted') {
                throw new Error('مجوز نوتفیکیشن داده نشد');
            }

            // 2. ثبت Service Worker
            const registration = await navigator.serviceWorker.register('/service-worker.js', {
                scope: '/'
            });

            // 3. دریافت VAPID Key
            const response = await fetch('/api/notifications/vapid-key/', {
                credentials: 'include'
            });
            const { public_key } = await response.json();

            // 4. تبدیل VAPID Key
            const applicationServerKey = urlBase64ToUint8Array(public_key);

            // 5. Subscribe
            const subscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: applicationServerKey
            });

            // 6. ارسال به سرور
            await fetch('/api/notifications/subscribe/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({
                    subscription: subscription.toJSON()
                })
            });

            setIsSubscribed(true);
        } catch (err) {
            setError(err.message);
            console.error('خطا در subscribe:', err);
        } finally {
            setIsLoading(false);
        }
    };

    const handleUnsubscribe = async () => {
        setIsLoading(true);
        setError(null);

        try {
            const registration = await navigator.serviceWorker.ready;
            const subscription = await registration.pushManager.getSubscription();
            
            if (subscription) {
                await subscription.unsubscribe();
                
                await fetch('/api/notifications/unsubscribe/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({
                        subscription: subscription.toJSON()
                    })
                });

                setIsSubscribed(false);
            }
        } catch (err) {
            setError(err.message);
            console.error('خطا در unsubscribe:', err);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div>
            {error && <div className="error">{error}</div>}
            {isSubscribed ? (
                <button onClick={handleUnsubscribe} disabled={isLoading}>
                    {isLoading ? 'در حال پردازش...' : 'غیرفعال کردن نوتفیکیشن'}
                </button>
            ) : (
                <button onClick={handleSubscribe} disabled={isLoading}>
                    {isLoading ? 'در حال پردازش...' : 'فعال کردن نوتفیکیشن'}
                </button>
            )}
        </div>
    );
}

export default NotificationButton;
```

---

## پشتیبانی

در صورت بروز مشکل، لطفاً با Backend Developer تماس بگیرید یا لاگ‌های مرورگر و Service Worker را بررسی کنید.

**لاگ‌های مفید:**
- Console مرورگر (F12)
- Service Worker Console (chrome://serviceworker-internals/)
- Network Tab برای بررسی درخواست‌های API

