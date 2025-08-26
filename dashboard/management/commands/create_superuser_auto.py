from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Create superuser automatically with default credentials'

    def handle(self, *args, **options):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin1234')
            self.stdout.write(self.style.SUCCESS('Superuser created: admin/admin1234'))
        else:
            self.stdout.write(self.style.WARNING('Superuser already exists'))