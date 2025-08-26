"""
Management Command: Process IVR Calls into Leads
Automatically converts IVR calls to leads with quality classification
"""
from django.core.management.base import BaseCommand
from dashboard.ivr_lead_creator import IVRLeadCreator

class Command(BaseCommand):
    help = 'Process IVR calls and create leads automatically'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--stats-only',
            action='store_true',
            help='Show statistics only, do not process calls'
        )
    
    def handle(self, *args, **options):
        creator = IVRLeadCreator()
        
        if options['stats_only']:
            # Show statistics only
            stats = creator.get_lead_statistics()
            
            self.stdout.write(self.style.SUCCESS('IVR Lead Statistics:'))
            self.stdout.write(f"Total IVR Leads: {stats['total_ivr_leads']}")
            self.stdout.write(f"Quality Leads: {stats['quality_leads']}")
            self.stdout.write(f"Junk Leads: {stats['junk_leads']}")
            
            self.stdout.write('\nBy Project:')
            for project, counts in stats['by_project'].items():
                self.stdout.write(f"  {project}: {counts['total']} total ({counts['quality']} quality, {counts['junk']} junk)")
            
            return
        
        # Process unprocessed calls
        self.stdout.write('Processing IVR calls into leads...')
        
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
            self.stdout.write(self.style.SUCCESS(f"\nSuccessfully processed {results['total_calls']} IVR calls into leads!"))
        else:
            self.stdout.write(self.style.WARNING("No unprocessed IVR calls found."))