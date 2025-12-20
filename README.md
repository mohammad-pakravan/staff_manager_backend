# Django Staff Management App

A comprehensive Django-based staff management application with authentication, role management, and center management features.

## Features

- **Authentication & Authorization**: JWT-based authentication with role-based access control
- **User Management**: Custom user model with roles (Employee, Food Admin, HR, System Admin)
- **Center Management**: Multi-center organization support
- **Food Management**: Complete food reservation system with weekly menu planning
- **Docker Support**: Complete Dockerization for development and production
- **REST API**: Full REST API with Django REST Framework
- **Report Generation**: PDF and Excel export functionality
- **API Documentation**: Complete Swagger/OpenAPI documentation
- **Persian Date Support**: Full support for Persian calendar

## 📚 API Documentation

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

### Documentation Files
- **Postman Collection**: [postman_collection.json](./postman_collection.json) - Complete API collection for testing

### Quick API Access
```bash
# Get JWT Token
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Use Token
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/food/meals/
```

## Quick Start

### 1. Environment Setup

Create a `.env` file in the project root:

```env
# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here
DJANGO_SETTINGS_MODULE=core.settings.dev

# Database Settings
DB_NAME=staff_db
DB_USER=staff_user
DB_PASSWORD=staff_pass
DB_HOST=localhost
DB_PORT=5432

# CORS Settings
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Allowed Hosts
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 2. Development with Docker

```bash
# Build and start development environment
docker-compose up --build

# The application will be available at http://localhost:8000
# Admin panel: http://localhost:8000/admin
# Default superuser: admin/admin123
```

### 3. Production Deployment

```bash
# Update .env for production
DEBUG=False
SECRET_KEY=your-production-secret-key
DJANGO_SETTINGS_MODULE=core.settings.prod
DB_NAME=your_prod_db
DB_USER=your_prod_user
DB_PASSWORD=your_prod_password
DB_HOST=your_prod_host
ALLOWED_HOSTS=your-domain.com

# Deploy
docker-compose -f docker-compose.yml -f compose/prod/docker-compose.prod.yml up -d --build
```

## API Endpoints

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `POST /api/auth/refresh/` - Refresh JWT token
- `GET /api/auth/me/` - Get current user info

### Centers
- `GET /api/centers/` - List centers (admin only)
- `POST /api/centers/` - Create center (admin only)
- `GET /api/centers/{id}/` - Get center details
- `PUT /api/centers/{id}/` - Update center (admin only)
- `DELETE /api/centers/{id}/` - Delete center (admin only)
- `GET /api/centers/{id}/employees/` - Get center employees

### Food Management
- `GET /api/food/meals/` - List meals
- `POST /api/food/meals/` - Create meal (food admin only)
- `GET /api/food/daily-menus/` - List daily menus
- `POST /api/food/reservations/` - Make food reservation
- `GET /api/food/reservations/` - List my reservations
- `POST /api/food/reservations/{id}/cancel/` - Cancel reservation
- `GET /api/food/statistics/` - Food statistics (admin only)
- `GET /api/food/centers/{id}/export/excel/` - Export Excel report
- `GET /api/food/centers/{id}/export/pdf/` - Export PDF report

## User Roles

1. **Employee**: Basic user with food reservation access
2. **Food Admin**: Can manage food-related operations and weekly menus
3. **HR**: Human resources with user management access
4. **System Admin**: Full system access

## Food Management Workflow

### For Employees:
1. **Login** → `POST /api/auth/login/`
2. **View Weekly Menu** → `GET /api/food/daily-menus/`
3. **Make Reservation** → `POST /api/food/reservations/`
4. **View My Reservations** → `GET /api/food/reservations/`
5. **Cancel Reservation** → `POST /api/food/reservations/{id}/cancel/`

### For Food Admins:
1. **Login** → `POST /api/auth/login/`
2. **Create Meals** → `POST /api/food/meals/`
3. **Create Weekly Menu** → `POST /api/food/weekly-menus/`
4. **View Reservations** → `GET /api/food/centers/{id}/reservations/`
5. **Export Reports** → `GET /api/food/centers/{id}/export/excel/`

## Project Structure

```
staff_manager/
├── compose/                 # Docker configurations
│   ├── dev/                # Development Docker setup
│   └── prod/               # Production Docker setup
├── core/                   # Django project core
│   ├── settings/           # Modular settings
│   └── urls.py
├── apps/                   # Django applications
│   ├── accounts/           # User management
│   ├── centers/            # Center management
│   └── food_management/    # Food reservation system
├── manage.py
├── requirements.txt
└── docker-compose.yml
```

## Development

### Local Development (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

### Database

The application uses PostgreSQL. Make sure PostgreSQL is running and accessible with the credentials specified in your `.env` file.

## Scheduled Tasks

### Story Expiry Cleanup

The application includes a management command to automatically clean up expired story files. This command should be run periodically (e.g., hourly or daily) using a cron job.

#### Command Usage

```bash
# Run cleanup manually
python manage.py cleanup_expired_stories

# Dry run (see what would be deleted without actually deleting)
python manage.py cleanup_expired_stories --dry-run

# In Docker
docker-compose exec web python manage.py cleanup_expired_stories
```

#### Setting up Cron Job

**On Linux/Mac:**

Add to crontab (`crontab -e`):

```bash
# Run every hour
0 * * * * cd /path/to/project && python manage.py cleanup_expired_stories

# Or run daily at 2 AM
0 2 * * * cd /path/to/project && python manage.py cleanup_expired_stories
```

**In Docker:**

Add to your docker-compose.yml or use a separate cron container:

```yaml
services:
  cron:
    image: your-django-image
    command: >
      sh -c "while true; do
        python manage.py cleanup_expired_stories;
        sleep 3600;
      done"
    volumes:
      - .:/app
    depends_on:
      - web
```

**What it does:**

- Finds all stories with `expiry_date` that has passed
- Deletes `thumbnail_image` and `content_file` from disk
- Clears the file fields in the database (keeps the record)
- Logs all operations for tracking

**Note:** Stories without `expiry_date` are never cleaned up automatically.

## License

This project is licensed under the MIT License.
