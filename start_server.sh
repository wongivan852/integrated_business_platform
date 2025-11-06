#!/bin/bash
# Startup script for Integrated Business Platform

cd /home/user/integrated_business_platform

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files (for production)
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Start Gunicorn
echo "Starting Gunicorn server..."
gunicorn business_platform.wsgi:application \
    --config gunicorn_config.py \
    --bind 0.0.0.0:8000 \
    --log-level info
