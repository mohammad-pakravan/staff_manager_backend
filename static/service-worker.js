// Service Worker برای Push Notifications

const CACHE_NAME = 'push-notifications-v1';

// نصب Service Worker
self.addEventListener('install', (event) => {
    console.log('Service Worker نصب شد');
    self.skipWaiting();
});

// فعال‌سازی Service Worker
self.addEventListener('activate', (event) => {
    console.log('Service Worker فعال شد');
    event.waitUntil(self.clients.claim());
});

// دریافت Push Notification
self.addEventListener('push', (event) => {
    console.log('🔔 Push Notification دریافت شد!', event);
    console.log('📦 Event data:', event.data);

    // Promise برای parse کردن و نمایش نوتفیکیشن
    const notificationPromise = (async () => {
        let data = {
            title: 'نوتفیکیشن جدید',
            body: 'پیام جدید دریافت شد',
            icon: null,
            badge: null,
            data: {},
            tag: 'notification'
        };

        // اگر داده‌ای همراه push باشد، از آن استفاده کن
        if (event.data) {
            try {
                let pushData;
                
                // بررسی اینکه event.data چه نوعی است
                if (typeof event.data.json === 'function') {
                    // json() یک Promise برمی‌گرداند
                    pushData = await event.data.json();
                } else if (typeof event.data.text === 'function') {
                    // text() یک Promise برمی‌گرداند
                    const text = await event.data.text();
                    pushData = JSON.parse(text);
                } else if (typeof event.data === 'string') {
                    pushData = JSON.parse(event.data);
                } else {
                    // اگر object است، مستقیماً استفاده کن
                    pushData = event.data;
                }
                
                console.log('📋 Parsed push data:', pushData);
                console.log('📋 Type of pushData:', typeof pushData);
                
                // استخراج داده‌ها
                if (pushData && typeof pushData === 'object') {
                    data.title = pushData.title || pushData.head || data.title;
                    data.body = pushData.body || pushData.message || data.body;
                    data.icon = pushData.icon || data.icon;
                    data.badge = pushData.badge || data.badge;
                    data.data = pushData.data || pushData || {};
                    data.url = pushData.url || (pushData.data && pushData.data.url) || null;
                    data.tag = pushData.tag || 'notification';
                    data.requireInteraction = pushData.requireInteraction || false;
                } else {
                    console.warn('⚠️ pushData یک object نیست:', pushData);
                }
            } catch (e) {
                console.error('❌ خطا در parse کردن JSON:', e);
                console.error('❌ Error details:', e.message, e.stack);
                // اگر JSON نبود، به صورت متن استفاده کن
                try {
                    let text;
                    if (typeof event.data.text === 'function') {
                        text = await event.data.text();
                    } else if (typeof event.data === 'string') {
                        text = event.data;
                    }
                    if (text) {
                        data.body = text;
                        console.log('📝 استفاده از متن ساده:', text);
                    }
                } catch (e2) {
                    console.error('❌ خطا در خواندن متن:', e2);
                }
            }
        } else {
            console.warn('⚠️ هیچ داده‌ای همراه push نیست');
        }

        console.log('✅ داده‌های نهایی:', data);

        // ساخت options برای نوتفیکیشن
        const options = {
            body: data.body || 'پیام جدید',
            data: data.data || {},
            vibrate: [200, 100, 200],
            tag: data.tag || 'notification',
            requireInteraction: data.requireInteraction || false
        };

        // اضافه کردن icon و badge فقط اگر وجود داشته باشند (null باعث خطا می‌شود)
        if (data.icon) {
            options.icon = data.icon;
        }
        if (data.badge) {
            options.badge = data.badge;
        }

        console.log('🎯 نمایش نوتفیکیشن با options:', options);
        console.log('📝 Title:', data.title);
        console.log('📝 Body:', data.body);

        // نمایش نوتفیکیشن
        try {
            await self.registration.showNotification(data.title || 'نوتفیکیشن جدید', options);
            console.log('✅ نوتفیکیشن با موفقیت نمایش داده شد!');
            console.log('📌 Title:', data.title);
            console.log('📌 Body:', data.body);
        } catch (error) {
            console.error('❌ خطا در نمایش نوتفیکیشن:', error);
            console.error('❌ Error details:', error.message, error.stack);
            // تلاش برای نمایش نوتفیکیشن ساده
            try {
                await self.registration.showNotification('نوتفیکیشن جدید', {
                    body: data.body || 'پیام جدید دریافت شد',
                    tag: 'notification-fallback'
                });
                console.log('✅ نوتفیکیشن fallback نمایش داده شد');
            } catch (fallbackError) {
                console.error('❌ خطا در نمایش نوتفیکیشن fallback:', fallbackError);
            }
        }
    })();

    event.waitUntil(notificationPromise);
});

// کلیک روی نوتفیکیشن
self.addEventListener('notificationclick', (event) => {
    console.log('کلیک روی نوتفیکیشن:', event);

    event.notification.close();

    const data = event.notification.data;
    let urlToOpen = '/';

    // اگر URL در داده‌ها باشد، از آن استفاده کن
    if (data && data.url) {
        urlToOpen = data.url;
    }

    event.waitUntil(
        clients.matchAll({
            type: 'window',
            includeUncontrolled: true
        }).then((clientList) => {
            // اگر پنجره باز است، به آن focus بده
            for (let client of clientList) {
                if (client.url === urlToOpen && 'focus' in client) {
                    return client.focus();
                }
            }
            // در غیر این صورت، پنجره جدید باز کن
            if (clients.openWindow) {
                return clients.openWindow(urlToOpen);
            }
        })
    );
});

// بستن نوتفیکیشن
self.addEventListener('notificationclose', (event) => {
    console.log('نوتفیکیشن بسته شد:', event);
});

// دریافت پیام از صفحه اصلی
self.addEventListener('message', (event) => {
    console.log('پیام دریافت شد از صفحه:', event.data);
    
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});

