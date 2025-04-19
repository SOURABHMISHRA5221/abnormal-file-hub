#!/bin/sh

# Ensure data directory exists and has proper permissions
mkdir -p /app/data
chmod -R 777 /app/data

# Create logs directory
mkdir -p /app/logs
chmod -R 777 /app/logs

# Run migrations
echo "Running migrations..."
python manage.py makemigrations
python manage.py migrate

# Start server with enhanced logging
echo "Starting server with debug logging..."
gunicorn --bind 0.0.0.0:8000 \
  --log-level=debug \
  --capture-output \
  --access-logfile=- \
  --error-logfile=- \
  core.wsgi:application 