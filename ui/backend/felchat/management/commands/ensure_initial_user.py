from django.core.management.base import BaseCommand
# from .models import User # If your models.py is in the same app
# Or, more robustly, if your app is 'felchat':
from felchat.models import User # Assuming your app is named 'felchat'

class Command(BaseCommand):
    help = 'Ensures at least one User record exists, creating one if the table is empty.'

    def handle(self, *args, **options):
        if not User.objects.exists():
            # No specific session_id needed, it will use the default uuid.uuid4
            user = User.objects.create()
            self.stdout.write(self.style.SUCCESS(f'Created an initial User record with session_id: {user.session_id}'))
        else:
            self.stdout.write(self.style.WARNING('User records already exist. No new initial user created.'))
