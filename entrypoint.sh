#!/bin/bash

set -e

# Wait for database to be ready (optional but good practice)
# echo "Waiting for database..."
# while ! nc -z $DB_HOST $DB_PORT; do
#   sleep 0.1
# done
# echo "Database is ready!"

# Run migrations
echo "Ejecutando migraciones..."
python manage.py migrate --no-input

# Collect static files
echo "Recolectando archivos estáticos..."
python manage.py collectstatic --no-input

# Start Gunicorn
echo "Iniciando Gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --log-level info \
    --access-logfile - \
    --error-logfile -
