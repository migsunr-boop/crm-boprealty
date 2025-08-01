from django.core.management.base import BaseCommand
from dashboard.tata_sync import TATASync

class Command(BaseCommand):
    help = 'Sync all data from TATA APIs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--templates-only',
            action='store_true',
            help='Sync only templates',
        )
        parser.add_argument(
            '--messages-only',
            action='store_true',
            help='Sync only messages',
        )

    def handle(self, *args, **options):
        sync = TATASync()
        
        self.stdout.write('Starting TATA data sync...')
        
        if options['templates_only']:
            result = sync.sync_templates()
            self.stdout.write(f"Templates sync: {result}")
        elif options['messages_only']:
            result = sync.sync_messages()
            self.stdout.write(f"Messages sync: {result}")
        else:
            results = sync.sync_all_data()
            self.stdout.write(f"Full sync completed: {results}")
        
        self.stdout.write(self.style.SUCCESS('TATA sync completed!'))