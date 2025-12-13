# ✅ چک‌لیست Production Deployment

این چک‌لیست را قبل از deploy کردن پروژه به production بررسی کنید.

## 🔐 امنیت

- [ ] `DEBUG=False` در `.env` تنظیم شده است
- [ ] `SECRET_KEY` قوی و منحصر به فرد تولید شده است
- [ ] `ALLOWED_HOSTS` شامل دامنه‌های production است
- [ ] فایل `.env` در `.gitignore` قرار دارد
- [ ] پسورد Database قوی است
- [ ] SSL/HTTPS تنظیم شده است (توصیه می‌شود)
- [ ] Firewall تنظیم شده است (فقط پورت‌های 80 و 443 باز هستند)

## 🗄️ Database

- [ ] Database PostgreSQL ایجاد شده است
- [ ] User Database با دسترسی‌های مناسب ایجاد شده است
- [ ] Migrations اجرا شده است
- [ ] Backup از Database گرفته شده است

## ⚙️ تنظیمات Environment

- [ ] فایل `.env` ایجاد شده است
- [ ] تمام متغیرهای محیطی تنظیم شده‌اند:
  - [ ] `DEBUG=False`
  - [ ] `SECRET_KEY` (قوی و منحصر به فرد)
  - [ ] `DJANGO_SETTINGS_MODULE=core.settings.prod`
  - [ ] `ALLOWED_HOSTS` (دامنه‌های production)
  - [ ] `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
  - [ ] `CORS_ALLOWED_ORIGINS` (دامنه‌های frontend)

## 🐳 Docker (اگر استفاده می‌کنید)

- [ ] Docker و Docker Compose نصب شده است
- [ ] فایل `docker-compose.prod.yml` بررسی شده است
- [ ] Container ها build شده‌اند
- [ ] Container ها در حال اجرا هستند

## 📁 Static و Media Files

- [ ] `collectstatic` اجرا شده است
- [ ] دایرکتوری `/app/staticfiles` وجود دارد
- [ ] دایرکتوری `/app/media` وجود دارد
- [ ] Permissions درست تنظیم شده است (755)
- [ ] Nginx برای serve کردن static files تنظیم شده است

## 🔄 Migrations

- [ ] تمام migrations اجرا شده‌اند
- [ ] هیچ migration pending نیست
- [ ] Database schema به‌روز است

## 👤 Superuser

- [ ] Superuser ایجاد شده است
- [ ] پسورد Superuser قوی است
- [ ] Superuser برای تست لاگین شده است

## 🌐 Nginx و SSL

- [ ] Nginx نصب و تنظیم شده است
- [ ] SSL Certificate دریافت شده است (Let's Encrypt)
- [ ] Nginx برای HTTPS تنظیم شده است
- [ ] Redirect از HTTP به HTTPS فعال است

## 📊 Monitoring و Logging

- [ ] Logging فعال است
- [ ] دایرکتوری `/app/logs` ایجاد شده است
- [ ] Log files قابل نوشتن هستند
- [ ] Monitoring setup شده است (اختیاری)

## 🔄 Backup

- [ ] Script backup ایجاد شده است
- [ ] Backup خودکار تنظیم شده است (Cron)
- [ ] Backup های قبلی تست شده‌اند

## 🧪 تست

- [ ] API endpoints تست شده‌اند
- [ ] Authentication کار می‌کند
- [ ] Static files لود می‌شوند
- [ ] Media files لود می‌شوند
- [ ] Database queries کار می‌کنند
- [ ] Admin panel قابل دسترسی است

## 📝 مستندات

- [ ] فایل `DEPLOYMENT.md` مطالعه شده است
- [ ] تمام مراحل deployment انجام شده است

---

## 🚀 دستورات سریع Deployment

### با Docker:
```bash
# 1. ایجاد فایل .env
cp .env.example .env
nano .env  # تنظیمات را ویرایش کنید

# 2. Build و Run
docker-compose -f compose/prod/docker-compose.prod.yml up -d --build

# 3. Migrations
docker-compose -f compose/prod/docker-compose.prod.yml exec web python manage.py migrate

# 4. Collectstatic
docker-compose -f compose/prod/docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# 5. ایجاد Superuser
docker-compose -f compose/prod/docker-compose.prod.yml exec web python manage.py createsuperuser

# 6. بررسی لاگ‌ها
docker-compose -f compose/prod/docker-compose.prod.yml logs -f
```

### بدون Docker:
```bash
# 1. ایجاد Virtual Environment
python3.11 -m venv venv
source venv/bin/activate

# 2. نصب Dependencies
pip install -r requirements.txt

# 3. تنظیم .env
nano .env

# 4. Migrations
python manage.py migrate

# 5. Collectstatic
python manage.py collectstatic --noinput

# 6. ایجاد Superuser
python manage.py createsuperuser

# 7. اجرا با Gunicorn
gunicorn --bind 0.0.0.0:8000 --workers 3 core.wsgi:application
```

---

## ⚠️ نکات مهم

1. **هرگز `SECRET_KEY` را در Git commit نکنید**
2. **فایل `.env` را در `.gitignore` قرار دهید**
3. **از HTTPS استفاده کنید**
4. **Backup های منظم داشته باشید**
5. **لاگ‌ها را به صورت منظم بررسی کنید**




