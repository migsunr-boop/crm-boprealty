from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import os

class Command(BaseCommand):
    help = 'Create superuser automatically with default credentials'

    def handle(self, *args, **options):
        # Always try to create/update superuser
        username = 'admin'
        email = 'admin@example.com'
        password = 'admin1234'
        
        try:
            user = User.objects.get(username=username)
            user.set_password(password)
            user.is_superuser = True
            user.is_staff = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Superuser updated: {username}/{password}'))
        except User.DoesNotExist:
            User.objects.create_superuser(username, email, password)
            self.stdout.write(self.style.SUCCESS(f'Superuser created: {username}/{password}'))
        
        # Also create from environment if available
        env_user = os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')
        env_pass = os.getenv('DJANGO_SUPERUSER_PASSWORD', 'admin1234')
        env_email = os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
        
        if env_user != username:
            try:
                user = User.objects.get(username=env_user)
                user.set_password(env_pass)
                user.is_superuser = True
                user.is_staff = True
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Env superuser updated: {env_user}'))
            except User.DoesNotExist:
                User.objects.create_superuser(env_user, env_email, env_pass)
                self.stdout.write(self.style.SUCCESS(f'Env superuser created: {env_user}'))