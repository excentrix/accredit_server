#!/bin/bash

python -m pip list
python -c "import django; print(django.get_version())"
# Apply database migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Start Gunicorn
gunicorn accredit.wsgi:application --bind=0.0.0.0:8000