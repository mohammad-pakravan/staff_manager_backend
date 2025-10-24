FROM python:3.11

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/staticfiles /app/media

# Collect static files
RUN python manage.py collectstatic --noinput

# Copy nginx configuration
COPY compose/prod/nginx.conf /etc/nginx/sites-available/default

# Make scripts executable
RUN chmod +x /app/compose/prod/django-entrypoint.sh

# Expose port
EXPOSE 8000

# Start command
CMD ["/app/compose/prod/django-entrypoint.sh"]


