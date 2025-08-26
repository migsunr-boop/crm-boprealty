"""
Sync IVR call data and process into leads
"""
from django.core.management.base import BaseCommand
from dashboard.models import IVRCallLog
from dashboard.ivr_lead_creator import IVRLeadCreator
from dashboard.tata_sync import TataSyncService

class Command(BaseCommand):
    help = 'Sync IVR data from TATA and process into leads'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--sync-first',
            action='store_true',
            help='Sync data from TATA API first, then process'
        )
    
    def handle(self, *args, **options):
        if options['sync_first']:
            # Sync data from TATA API first
            self.stdout.write('Syncing IVR data from TATA API...')
            sync_service = TataSyncService()
            try:
                sync_result = sync_service.sync_call_logs()
                self.stdout.write(f"Synced {sync_result.get('new_calls', 0)} new calls")
            except Exception as e:
                self.stdout.write(f"Sync error: {e}")
        
        # Check current IVR calls
        total_calls = IVRCallLog.objects.count()
        unprocessed_calls = IVRCallLog.objects.filter(processed=False).count()
        
        self.stdout.write(f"Total IVR calls in database: {total_calls}")
        self.stdout.write(f"Unprocessed calls: {unprocessed_calls}")
        
        if unprocessed_calls == 0:
            self.stdout.write(self.style.WARNING("No unprocessed calls found. All calls may already be processed."))
            return
        
        # Process calls into leads
        self.stdout.write('Processing IVR calls into leads...')
        creator = IVRLeadCreator()
        results = creator.process_unprocessed_calls()
        
        # Display results
        self.stdout.write(f"\nProcessing Results:")
        self.stdout.write(f"Total calls processed: {results['total_calls']}")
        self.stdout.write(f"New leads created: {results['new_leads']}")
        self.stdout.write(f"Existing leads updated: {results['updated_leads']}")
        self.stdout.write(f"Quality leads: {results['quality_leads']}")
        self.stdout.write(f"Junk leads: {results['junk_leads']}")
        
        if results['errors']:
            self.stdout.write(self.style.ERROR(f"\nErrors ({len(results['errors'])}):"))
            for error in results['errors']:
                self.stdout.write(f"  - {error}")
        
        if results['total_calls'] > 0:
            self.stdout.write(self.style.SUCCESS(f"\n✅ Successfully processed {results['total_calls']} IVR calls into leads!"))
        
        # Show final stats
        from dashboard.models import Lead
        ivr_leads = Lead.objects.filter(source='ivr_call').count()
        self.stdout.write(f"\nTotal IVR leads in system: {ivr_leads}")