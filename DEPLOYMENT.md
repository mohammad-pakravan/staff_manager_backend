# راهنمای کامل Deployment برای Production

این راهنما شامل تمام مراحل لازم برای deploy کردن پروژه Django روی production است.

## 📋 فهرست مطالب

1. [پیش‌نیازها](#پیش‌نیازها)
2. [تنظیمات Environment Variables](#تنظیمات-environment-variables)
3. [تنظیمات امنیتی](#تنظیمات-امنیتی)
4. [تنظیمات Database](#تنظیمات-database)
5. [تنظیمات SSL/HTTPS](#تنظیمات-sslhttps)
6. [Deployment با Docker](#deployment-با-docker)
7. [Deployment بدون Docker](#deployment-بدون-docker)
8. [بررسی و تست](#بررسی-و-تست)
9. [Backup و Monitoring](#backup-و-monitoring)

---

## پیش‌نیازها

### 1. سرور
- سرور لینوکس (Ubuntu 20.04+ یا Debian 11+ توصیه می‌شود)
- حداقل 2GB RAM
- حداقل 20GB فضای دیسک
- دسترسی root یا sudo

### 2. نرم‌افزارهای مورد نیاز
```bash
# Docker و Docker Compose
sudo apt-get update
sudo apt-get install -y docker.io docker-compose

# PostgreSQL (اگر از Docker استفاده نمی‌کنید)
sudo apt-get install -y postgresql postgresql-contrib

# Nginx (اگر از Docker استفاده نمی‌کنید)
sudo apt-get install -y nginx

# Python 3.11+ (اگر از Docker استفاده نمی‌کنید)
sudo apt-get install -y python3.11 python3.11-venv python3-pip
```

---

## تنظیمات Environment Variables

### 1. ایجاد فایل `.env`

در root پروژه فایل `.env` ایجاد کنید:

```bash
cd /path/to/charity-django-backend/staff_manager
nano .env
```

### 2. محتوای فایل `.env` برای Production

```env
# ============================================
# Django Settings
# ============================================
DEBUG=False
SECRET_KEY=your-super-secret-key-here-change-this-in-production-min-50-chars
DJANGO_SETTINGS_MODULE=core.settings.prod
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,api.yourdomain.com

# ============================================
# Database Settings
# ============================================
DB_NAME=charity_db_prod
DB_USER=charity_db_user
DB_PASSWORD=your-strong-database-password-here
DB_HOST=db
DB_PORT=5432

# ============================================
# CORS Settings
# ============================================
# لیست دامنه‌های frontend که اجازه دسترسی دارند
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# ============================================
# Security Settings (اختیاری)
# ============================================
# برای استفاده از HTTPS
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# ============================================
# Email Settings (اگر نیاز دارید)
# ============================================
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_USE_TLS=True
# EMAIL_HOST_USER=your-email@gmail.com
# EMAIL_HOST_PASSWORD=your-app-password
```

### 3. تولید SECRET_KEY

```bash
# در Python shell
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

یا از این دستور استفاده کنید:
```bash
python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## تنظیمات امنیتی

### 1. بررسی فایل `prod.py`

اطمینان حاصل کنید که تنظیمات امنیتی در `core/settings/prod.py` فعال هستند:

```python
DEBUG = False
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

### 2. تنظیمات اضافی برای HTTPS

اگر از HTTPS استفاده می‌کنید، این تنظیمات را به `prod.py` اضافه کنید:

```python
# HTTPS Settings
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=False, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=False, cast=bool)
```

---

## تنظیمات Database

### 1. با Docker (توصیه می‌شود)

Database به صورت خودکار در Docker container اجرا می‌شود. فقط باید تنظیمات `.env` را درست کنید.

### 2. بدون Docker

```bash
# ورود به PostgreSQL
sudo -u postgres psql

# ایجاد Database و User
CREATE DATABASE charity_db_prod;
CREATE USER charity_db_user WITH PASSWORD 'your-strong-password';
ALTER ROLE charity_db_user SET client_encoding TO 'utf8';
ALTER ROLE charity_db_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE charity_db_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE charity_db_prod TO charity_db_user;
\q
```

---

## تنظیمات SSL/HTTPS

### 1. دریافت SSL Certificate با Let's Encrypt

```bash
# نصب Certbot
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx

# دریافت Certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# تمدید خودکار
sudo certbot renew --dry-run
```

### 2. تنظیم Nginx برای HTTPS

اگر از Docker استفاده نمی‌کنید، فایل Nginx را به‌روزرسانی کنید:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    client_max_body_size 20M;

    # Static files
    location /static/ {
        alias /app/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /app/media/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # API and admin
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
}
```

---

## Deployment با Docker

### 1. آماده‌سازی

```bash
# کلون کردن پروژه (یا آپلود فایل‌ها)
cd /opt
git clone <your-repo-url> charity-django-backend
cd charity-django-backend/staff_manager

# ایجاد فایل .env
nano .env
# (محتویات .env را از بالا کپی کنید)
```

### 2. Build و Run

```bash
# Build و Start
docker-compose -f compose/prod/docker-compose.prod.yml up -d --build

# بررسی لاگ‌ها
docker-compose -f compose/prod/docker-compose.prod.yml logs -f

# بررسی وضعیت
docker-compose -f compose/prod/docker-compose.prod.yml ps
```

### 3. اجرای Migrations

```bash
# اجرای migrations
docker-compose -f compose/prod/docker-compose.prod.yml exec web python manage.py migrate

# ایجاد superuser (اگر نیاز دارید)
docker-compose -f compose/prod/docker-compose.prod.yml exec web python manage.py createsuperuser

# جمع‌آوری static files
docker-compose -f compose/prod/docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

### 4. مدیریت Container

```bash
# Restart
docker-compose -f compose/prod/docker-compose.prod.yml restart

# Stop
docker-compose -f compose/prod/docker-compose.prod.yml stop

# Start
docker-compose -f compose/prod/docker-compose.prod.yml start

# Stop و Remove
docker-compose -f compose/prod/docker-compose.prod.yml down

# Stop و Remove با volumes (⚠️ حذف داده‌ها)
docker-compose -f compose/prod/docker-compose.prod.yml down -v
```

---

## Deployment بدون Docker

### 1. نصب Dependencies

```bash
# ایجاد Virtual Environment
python3.11 -m venv venv
source venv/bin/activate

# نصب Dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. تنظیمات Database

```bash
# اجرای Migrations
python manage.py migrate

# ایجاد Superuser
python manage.py createsuperuser

# جمع‌آوری Static Files
python manage.py collectstatic --noinput
```

### 3. اجرا با Gunicorn

```bash
# نصب Gunicorn (اگر در requirements.txt نیست)
pip install gunicorn

# اجرا
gunicorn --bind 0.0.0.0:8000 --workers 3 --timeout 120 core.wsgi:application
```

### 4. تنظیم Systemd Service

ایجاد فایل `/etc/systemd/system/charity-django.service`:

```ini
[Unit]
Description=Charity Django Backend
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/charity-django-backend/staff_manager
Environment="PATH=/opt/charity-django-backend/staff_manager/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=core.settings.prod"
ExecStart=/opt/charity-django-backend/staff_manager/venv/bin/gunicorn \
    --workers 3 \
    --timeout 120 \
    --bind 127.0.0.1:8000 \
    --access-logfile /var/log/charity-django/access.log \
    --error-logfile /var/log/charity-django/error.log \
    core.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
# فعال‌سازی Service
sudo systemctl daemon-reload
sudo systemctl enable charity-django
sudo systemctl start charity-django

# بررسی وضعیت
sudo systemctl status charity-django

# مشاهده لاگ‌ها
sudo journalctl -u charity-django -f
```

---

## بررسی و تست

### 1. بررسی Health Check

```bash
# بررسی API
curl http://localhost:8000/api/server-time/

# بررسی Admin Panel
curl -I http://localhost:8000/admin/

# بررسی API Docs
curl -I http://localhost:8000/api/docs/
```

### 2. بررسی Database Connection

```bash
# با Docker
docker-compose -f compose/prod/docker-compose.prod.yml exec web python manage.py dbshell

# بدون Docker
python manage.py dbshell
```

### 3. بررسی Static Files

```bash
# بررسی وجود فایل‌های static
ls -la /app/staticfiles/
ls -la /app/media/
```

### 4. تست API

```bash
# Login
curl -X POST http://yourdomain.com/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}'

# استفاده از Token
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://yourdomain.com/api/auth/me/
```

---

## Backup و Monitoring

### 1. Backup Database

```bash
# با Docker
docker-compose -f compose/prod/docker-compose.prod.yml exec db pg_dump -U charity_db_user charity_db_prod > backup_$(date +%Y%m%d_%H%M%S).sql

# بدون Docker
pg_dump -U charity_db_user charity_db_prod > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore
psql -U charity_db_user charity_db_prod < backup_20250101_120000.sql
```

### 2. Backup Media Files

```bash
# Backup media directory
tar -czf media_backup_$(date +%Y%m%d_%H%M%S).tar.gz /app/media/
```

### 3. Script Backup خودکار

ایجاد فایل `/opt/backup-charity.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# ایجاد دایرکتوری backup
mkdir -p $BACKUP_DIR

# Backup Database
docker-compose -f /opt/charity-django-backend/staff_manager/compose/prod/docker-compose.prod.yml exec -T db pg_dump -U charity_db_user charity_db_prod > $BACKUP_DIR/db_$DATE.sql

# Backup Media
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /opt/charity-django-backend/staff_manager/media/

# حذف backup های قدیمی‌تر از 7 روز
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

```bash
# قابل اجرا کردن
chmod +x /opt/backup-charity.sh

# اضافه کردن به Crontab (هر روز ساعت 2 صبح)
crontab -e
# اضافه کردن این خط:
0 2 * * * /opt/backup-charity.sh
```

### 4. Monitoring

```bash
# بررسی لاگ‌های Django
tail -f /app/logs/django.log

# بررسی لاگ‌های Gunicorn
tail -f /app/logs/gunicorn_error.log

# بررسی استفاده از منابع
docker stats

# بررسی فضای دیسک
df -h
```

---

## نکات مهم

### 1. امنیت
- ✅ هرگز `SECRET_KEY` را در Git commit نکنید
- ✅ فایل `.env` را در `.gitignore` قرار دهید
- ✅ از پسوردهای قوی برای Database استفاده کنید
- ✅ `DEBUG=False` در production
- ✅ از HTTPS استفاده کنید
- ✅ Firewall را تنظیم کنید (فقط پورت‌های 80 و 443 باز باشند)

### 2. Performance
- ✅ تعداد workers Gunicorn را بر اساس CPU cores تنظیم کنید
- ✅ از CDN برای static files استفاده کنید (اختیاری)
- ✅ Database indexes را بررسی کنید
- ✅ از Caching استفاده کنید (Redis - اختیاری)

### 3. Maintenance
- ✅ به‌روزرسانی‌های امنیتی را بررسی کنید
- ✅ Backup های منظم داشته باشید
- ✅ لاگ‌ها را بررسی کنید
- ✅ فضای دیسک را مانیتور کنید

---

## Troubleshooting

### مشکل: Database connection failed
```bash
# بررسی وضعیت Database
docker-compose -f compose/prod/docker-compose.prod.yml ps db

# بررسی لاگ‌های Database
docker-compose -f compose/prod/docker-compose.prod.yml logs db
```

### مشکل: Static files نمایش داده نمی‌شوند
```bash
# جمع‌آوری مجدد static files
docker-compose -f compose/prod/docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# بررسی permissions
chmod -R 755 /app/staticfiles
chmod -R 755 /app/media
```

### مشکل: 502 Bad Gateway
```bash
# بررسی وضعیت Gunicorn
docker-compose -f compose/prod/docker-compose.prod.yml ps web

# بررسی لاگ‌های Gunicorn
docker-compose -f compose/prod/docker-compose.prod.yml logs web
```

---

## پشتیبانی

در صورت بروز مشکل، لاگ‌ها را بررسی کنید:
- Django logs: `/app/logs/django.log`
- Gunicorn logs: `/app/logs/gunicorn_error.log` و `/app/logs/gunicorn_access.log`
- Nginx logs: `/var/log/nginx/error.log`

