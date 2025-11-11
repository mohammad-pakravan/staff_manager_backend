#!/bin/sh

# Wait for database
echo "Waiting for database..."
while ! pg_isready -h db -p 5432; do
  sleep 1
done
echo "Database started"

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Start nginx in background
echo "Starting nginx..."
nginx

# Start gunicorn
echo "Starting gunicorn..."
gunicorn --config /app/compose/prod/gunicorn.conf.py core.wsgi:application