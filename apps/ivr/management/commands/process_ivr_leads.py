"""
Django Management Command: Process IVR Leads for WhatsApp Campaign
Usage: python manage.py process_ivr_leads --dry-run --limit 5
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.ivr.tasks import IVRLeadProcessor
import json

class Command(BaseCommand):
    help = 'Process IVR leads and send WhatsApp template messages'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview payloads without sending messages'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of messages to send'
        )
        parser.add_argument(
            '--template',
            type=str,
            default='project_update_template',
            help='WhatsApp template name to use'
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']
        template_name = options['template']
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting IVR lead processing (dry_run={dry_run})')
        )
        
        processor = IVRLeadProcessor()
        results = processor.process_ivr_leads(dry_run=dry_run)
        
        # Display results
        self.stdout.write(f"Total calls processed: {results['total_calls']}")
        self.stdout.write(f"Unique valid calls: {results['unique_calls']}")
        self.stdout.write(f"WhatsApp messages queued: {len(results['whatsapp_queue'])}")
        
        # Show grouped data preview
        self.stdout.write("\n--- Grouped Data Preview ---")
        for project, statuses in results['grouped_data'].items():
            self.stdout.write(f"\nProject: {project}")
            for status, calls in statuses.items():
                self.stdout.write(f"  {status}: {len(calls)} calls")
        
        # Show WhatsApp payloads (first 5)
        if results['whatsapp_queue']:
            self.stdout.write("\n--- WhatsApp Payloads (First 5) ---")
            for i, payload in enumerate(results['whatsapp_queue'][:5]):
                self.stdout.write(f"\n{i+1}. To: {payload['to']}")
                self.stdout.write(f"   Template: {payload['template']['name']}")
                if 'body_variables' in payload:
                    self.stdout.write(f"   Variables: {payload['body_variables']}")
                if 'header_media_url' in payload:
                    self.stdout.write(f"   Media: {payload['header_media_url']}")
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('\nDRY RUN - No messages were actually sent')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'\nProcessing completed - {len(results["whatsapp_queue"])} messages sent')
            )