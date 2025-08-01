web: python manage.py collectstatic --noinput && gunicorn realty_dashboard.wsgi:application --bind 0.0.0.0:$PORT
release: python manage.py makemigrations && python manage.py migrate