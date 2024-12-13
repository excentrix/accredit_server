#!/bin/bash
set -e

# Make migrations
echo "Making migrations..."
python manage.py makemigrations

echo "Applying migrations..."
python manage.py migrate --no-input

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Starting Gunicorn..."
exec gunicorn --workers=3 \
    --bind 0.0.0.0:8000 \
    accredit.wsgi:application \
    --timeout 300 \
    --access-logfile - \
    --error-logfile - \
    --log-level debug