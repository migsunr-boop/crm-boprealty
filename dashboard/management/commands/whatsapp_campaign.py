"""
Django management command for WhatsApp campaigns
Production-grade CLI interface for campaign execution
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import datetime, timedelta
import json
import csv
import sys
from dashboard.tata_whatsapp_service import TataWhatsAppCampaignService
from dashboard.models import Project, Lead

class Command(BaseCommand):
    help = 'Execute WhatsApp template campaigns for IVR leads'

    def add_arguments(self, parser):
        # Required arguments
        parser.add_argument(
            '--template-name',
            type=str,
            required=True,
            help='WhatsApp template name (must exist in Tata Omnichannel)'
        )
        
        parser.add_argument(
            '--from-date',
            type=str,
            required=True,
            help='Start date for lead filtering (YYYY-MM-DD)'
        )
        
        parser.add_argument(
            '--to-date',
            type=str,
            required=True,
            help='End date for lead filtering (YYYY-MM-DD)'
        )
        
        # Optional arguments
        parser.add_argument(
            '--projects',
            nargs='+',
            help='Project names to filter leads (space-separated)'
        )
        
        parser.add_argument(
            '--language',
            type=str,
            default='en',
            choices=['en', 'hi'],
            help='Template language code (default: en)'
        )
        
        parser.add_argument(
            '--header-media-url',
            type=str,
            help='Public URL for header media (image/video/document)'
        )
        
        parser.add_argument(
            '--header-media-type',
            type=str,
            choices=['image', 'video', 'document'],
            help='Type of header media'
        )
        
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Maximum number of messages to send (default: 100)'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview mode - don\'t send actual messages'
        )
        
        parser.add_argument(
            '--export-csv',
            type=str,
            help='Export results to CSV file'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompts'
        )

    def handle(self, *args, **options):
        try:
            # Parse and validate dates
            from_date = self.parse_date(options['from_date'])
            to_date = self.parse_date(options['to_date'])
            
            # Validate date range
            if from_date > to_date:
                raise CommandError('From date cannot be after to date')
            
            if (to_date - from_date).days > 90:
                raise CommandError('Date range cannot exceed 90 days')
            
            # Validate template name
            template_name = options['template_name'].strip()
            if not template_name:
                raise CommandError('Template name cannot be empty')
            
            # Validate media parameters
            media_url = options.get('header_media_url', '').strip()
            media_type = options.get('header_media_type', '').strip()
            
            if media_url and not media_type:
                raise CommandError('Media type required when media URL provided')
            
            if media_type and not media_url:
                raise CommandError('Media URL required when media type provided')
            
            # Initialize campaign service
            campaign_service = TataWhatsAppCampaignService()
            
            # Get preview of leads
            self.stdout.write(self.style.HTTP_INFO('Analyzing leads...'))
            
            leads = campaign_service.get_ivr_leads(
                project_names=options.get('projects', []),
                from_date=from_date,
                to_date=to_date,
                limit=options['limit']
            )
            
            if not leads:
                self.stdout.write(self.style.WARNING('No valid leads found for the specified criteria'))
                return
            
            # Display preview
            self.display_campaign_preview(leads, options)
            
            # Confirmation (unless --force)
            if not options['force'] and not options['dry_run']:
                confirm = input('\nProceed with sending messages? (yes/no): ')
                if confirm.lower() not in ['yes', 'y']:
                    self.stdout.write(self.style.WARNING('Campaign cancelled'))
                    return
            
            # Execute campaign
            self.stdout.write(self.style.HTTP_INFO('Executing campaign...'))
            
            results = campaign_service.run_campaign(
                project_names=options.get('projects', []),
                from_date=from_date,
                to_date=to_date,
                template_name=template_name,
                language=options['language'],
                header_media_url=media_url or None,
                header_media_type=media_type or None,
                dry_run=options['dry_run'],
                limit=options['limit']
            )
            
            # Display results
            self.display_results(results, options)
            
            # Export to CSV if requested
            if options.get('export_csv'):
                self.export_to_csv(results, options['export_csv'])
            
        except Exception as e:
            raise CommandError(f'Campaign failed: {str(e)}')

    def parse_date(self, date_str):
        """Parse date string to datetime object"""
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            raise CommandError(f'Invalid date format: {date_str}. Use YYYY-MM-DD')

    def display_campaign_preview(self, leads, options):
        """Display campaign preview information"""
        self.stdout.write(self.style.SUCCESS('\n=== CAMPAIGN PREVIEW ==='))
        
        # Campaign parameters
        self.stdout.write(f"Template: {options['template_name']}")
        self.stdout.write(f"Language: {options['language']}")
        self.stdout.write(f"Date Range: {options['from_date']} to {options['to_date']}")
        
        if options.get('projects'):
            self.stdout.write(f"Projects: {', '.join(options['projects'])}")
        else:
            self.stdout.write("Projects: All projects")
        
        if options.get('header_media_url'):
            self.stdout.write(f"Media: {options['header_media_type']} - {options['header_media_url']}")
        
        self.stdout.write(f"Limit: {options['limit']}")
        self.stdout.write(f"Mode: {'DRY RUN' if options['dry_run'] else 'LIVE SEND'}")
        
        # Lead statistics
        self.stdout.write(f"\nTotal Leads Found: {len(leads)}")
        
        # Project breakdown
        project_counts = {}
        for lead in leads:
            for project in lead.interested_projects.all():
                project_counts[project.name] = project_counts.get(project.name, 0) + 1
        
        if project_counts:
            self.stdout.write("\nProject Breakdown:")
            for project, count in sorted(project_counts.items()):
                self.stdout.write(f"  {project}: {count} leads")
        
        # Sample leads
        self.stdout.write("\nSample Leads:")
        for i, lead in enumerate(leads[:5]):
            masked_phone = lead.phone[:-4] + 'XXXX' if len(lead.phone) > 4 else 'XXXX'
            self.stdout.write(f"  {i+1}. {lead.name} ({masked_phone}) - {lead.created_at.strftime('%Y-%m-%d')}")
        
        if len(leads) > 5:
            self.stdout.write(f"  ... and {len(leads) - 5} more")

    def display_results(self, results, options):
        """Display campaign execution results"""
        self.stdout.write(self.style.SUCCESS('\n=== CAMPAIGN RESULTS ==='))
        
        # Summary statistics
        self.stdout.write(f"Total Leads: {results['total_leads']}")
        self.stdout.write(f"Valid Leads: {results['valid_leads']}")
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING(f"DRY RUN - Would send: {results['sent_count']} messages"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Messages Sent: {results['sent_count']}"))
            self.stdout.write(self.style.ERROR(f"Messages Failed: {results['failed_count']}"))
        
        # Success rate
        if results['valid_leads'] > 0:
            success_rate = (results['sent_count'] / results['valid_leads']) * 100
            self.stdout.write(f"Success Rate: {success_rate:.1f}%")
        
        # Display errors
        if results['errors']:
            self.stdout.write(self.style.ERROR('\nErrors:'))
            for error in results['errors'][:10]:  # Show first 10 errors
                self.stdout.write(f"  - {error}")
            
            if len(results['errors']) > 10:
                self.stdout.write(f"  ... and {len(results['errors']) - 10} more errors")
        
        # Display failed messages
        if results['failed_messages']:
            self.stdout.write(self.style.ERROR('\nFailed Messages:'))
            for failed in results['failed_messages'][:5]:  # Show first 5 failures
                self.stdout.write(f"  - {failed['lead_name']}: {failed['error']}")
            
            if len(results['failed_messages']) > 5:
                self.stdout.write(f"  ... and {len(results['failed_messages']) - 5} more failures")

    def export_to_csv(self, results, filename):
        """Export campaign results to CSV"""
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow([
                    'Lead ID', 'Lead Name', 'Phone', 'Status', 'Message ID', 'Error'
                ])
                
                # Write successful messages
                for msg in results['sent_messages']:
                    writer.writerow([
                        msg['lead_id'],
                        msg['lead_name'],
                        msg['phone'],
                        'sent',
                        msg.get('message_id', ''),
                        ''
                    ])
                
                # Write failed messages
                for msg in results['failed_messages']:
                    writer.writerow([
                        msg['lead_id'],
                        msg['lead_name'],
                        msg['phone'],
                        'failed',
                        '',
                        msg['error']
                    ])
            
            self.stdout.write(self.style.SUCCESS(f'\nResults exported to: {filename}'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to export CSV: {str(e)}'))

    def handle_error(self, error_msg):
        """Handle and display errors consistently"""
        self.stdout.write(self.style.ERROR(f'ERROR: {error_msg}'))
        sys.exit(1)