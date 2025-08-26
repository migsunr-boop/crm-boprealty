import os
import django
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'realty_dashboard.settings')
django.setup()

from dashboard.tata_calls_api import TATACallsAPI
from dashboard.models import IVRCallLog, Lead

class Command(BaseCommand):
    help = 'Sync call data from TATA API'
    
    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=7, help='Number of days to sync (default: 7)')
        parser.add_argument('--full-sync', action='store_true', help='Perform full sync (30 days)')
    
    def handle(self, *args, **options):
        self.stdout.write('Starting TATA data sync...')
        
        days = 30 if options['full_sync'] else options['days']
        
        try:
            tata_api = TATACallsAPI()
            
            # Calculate date range
            to_date = timezone.now()
            from_date = to_date - timedelta(days=days)
            
            self.stdout.write(f'Syncing data from {from_date.date()} to {to_date.date()}')
            
            # Fetch call records
            page = 1
            total_synced = 0
            
            while True:
                result = tata_api.get_call_records(
                    from_date.strftime('%Y-%m-%d %H:%M:%S'),
                    to_date.strftime('%Y-%m-%d %H:%M:%S'),
                    page=page,
                    limit=100
                )
                
                if not result.get('success', True) or not result.get('results'):
                    break
                
                calls = result.get('results', [])
                
                for call_data in calls:
                    try:
                        # Create or update call log
                        call_log, created = IVRCallLog.objects.get_or_create(
                            uuid=call_data.get('uuid', call_data.get('call_id')),
                            defaults={
                                'call_to_number': call_data.get('did_number', ''),
                                'caller_id_number': call_data.get('client_number', ''),
                                'call_id': call_data.get('call_id', ''),
                                'start_stamp': self.parse_datetime(call_data.get('date'), call_data.get('time')),
                                'duration': call_data.get('call_duration', 0),
                                'status': call_data.get('status', 'unknown'),
                                'raw_data': call_data,
                                'billing_circle': call_data.get('circle', {}).get('circle', ''),
                                'customer_no_with_prefix': call_data.get('client_number', '')
                            }
                        )
                        
                        if created:
                            # Try to associate with existing lead
                            call_log.associate_with_lead()
                            total_synced += 1
                            
                    except Exception as e:
                        self.stdout.write(f'Error processing call {call_data.get("call_id")}: {e}')
                
                # Check if there are more pages
                if len(calls) < 100:
                    break
                
                page += 1
                
                if page > 50:  # Safety limit
                    break
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully synced {total_synced} new call records')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during sync: {e}')
            )
    
    def parse_datetime(self, date_str, time_str):
        """Parse TATA date/time format"""
        try:
            from datetime import datetime
            if date_str and time_str:
                datetime_str = f"{date_str} {time_str}"
                return datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
        except:
            pass
        return timezone.now()