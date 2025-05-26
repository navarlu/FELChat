# your_app_name/management/commands/ensure_initial_user.py
from django.core.management.base import BaseCommand
from felchat.models import User # Or your_app_name.models

class Command(BaseCommand):
    help = 'Ensures at least one User record exists...'

    def handle(self, *args, **options):
        # ... your logic ...
        if not User.objects.exists():
            user = User.objects.create()
            self.stdout.write(self.style.SUCCESS(f'Created an initial User record with session_id: {user.session_id}'))
        else:
            self.stdout.write(self.style.WARNING('User records already exist. No new initial user created.'))
