"""
Django Management Command: Process IVR Leads for WhatsApp Campaign
Usage: python manage.py process_ivr_whatsapp --dry-run --limit 5
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from dashboard.ivr_integration import IVRLeadProcessor
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
        parser.add_argument(
            '--test-numbers',
            nargs='+',
            help='Send to specific test numbers only'
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']
        template_name = options['template']
        test_numbers = options.get('test_numbers', [])
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting IVR WhatsApp Campaign (dry_run={dry_run})')
        )
        
        if test_numbers:
            self.stdout.write(f'Test mode: {len(test_numbers)} numbers')
        
        processor = IVRLeadProcessor()
        results = processor.process_ivr_leads(dry_run=dry_run)
        
        # Filter for test numbers if specified
        if test_numbers:
            filtered_queue = []
            for payload in results['whatsapp_queue']:
                phone = payload['to']
                if any(test_num in phone for test_num in test_numbers):
                    filtered_queue.append(payload)
            results['whatsapp_queue'] = filtered_queue
        
        # Apply limit
        if limit:
            results['whatsapp_queue'] = results['whatsapp_queue'][:limit]
        
        # Display results
        self.stdout.write(f"\nProcessing Results:")
        self.stdout.write(f"   Total IVR calls: {results['total_calls']}")
        self.stdout.write(f"   Unique valid calls: {results['unique_calls']}")
        self.stdout.write(f"   WhatsApp messages queued: {len(results['whatsapp_queue'])}")
        
        # Show grouped data preview
        self.stdout.write(f"\nGrouped Data Preview:")
        for project, statuses in results['grouped_data'].items():
            self.stdout.write(f"   {project}:")
            for status, calls in statuses.items():
                self.stdout.write(f"      {status}: {len(calls)} calls")
        
        # Show WhatsApp payloads
        if results['whatsapp_queue']:
            self.stdout.write(f"\nWhatsApp Payloads (First 5):")
            for i, payload in enumerate(results['whatsapp_queue'][:5]):
                self.stdout.write(f"\n   {i+1}. To: {payload['to']}")
                self.stdout.write(f"      Template: {payload['template']['name']}")
                if 'body_variables' in payload:
                    self.stdout.write(f"      Variables: {payload['body_variables']}")
                if 'header_media_url' in payload:
                    self.stdout.write(f"      Media: {payload['header_media_url']}")
                
                # Show send result if available
                if 'send_result' in payload:
                    result = payload['send_result']
                    status_icon = "[SUCCESS]" if result['success'] else "[FAILED]"
                    self.stdout.write(f"      {status_icon} Result: {result['message_id']}")
        
        # Summary
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'\nDRY RUN COMPLETED - No messages were actually sent')
            )
            self.stdout.write(f'   Ready to send {len(results["whatsapp_queue"])} messages')
        else:
            sent_count = sum(1 for p in results['whatsapp_queue'] if p.get('send_result', {}).get('success'))
            failed_count = len(results['whatsapp_queue']) - sent_count
            
            self.stdout.write(
                self.style.SUCCESS(f'\nCAMPAIGN COMPLETED')
            )
            self.stdout.write(f'   Messages sent: {sent_count}')
            self.stdout.write(f'   Messages failed: {failed_count}')
        
        # Next steps
        self.stdout.write(f'\nNext Steps:')
        if dry_run:
            self.stdout.write(f'   1. Verify template "{template_name}" exists in Tata panel')
            self.stdout.write(f'   2. Test with internal numbers: --test-numbers +919876543210')
            self.stdout.write(f'   3. Run live: python manage.py process_ivr_whatsapp --limit 5')
        else:
            self.stdout.write(f'   1. Monitor delivery receipts in dashboard')
            self.stdout.write(f'   2. Check WhatsApp message logs')
            self.stdout.write(f'   3. Verify campaign performance')
        
        self.stdout.write(f'\nCampaign Summary: {len(results["whatsapp_queue"])} messages processed')