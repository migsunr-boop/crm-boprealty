"""
Fix phone numbers in database to E.164 format for WhatsApp
"""
from django.core.management.base import BaseCommand
from dashboard.models import Lead
import re

class Command(BaseCommand):
    help = 'Fix phone numbers to E.164 format for WhatsApp campaigns'

    def handle(self, *args, **options):
        leads = Lead.objects.all()
        fixed_count = 0
        
        for lead in leads:
            if lead.phone:
                # Clean phone number
                clean_phone = re.sub(r'[^\d+]', '', lead.phone)
                
                # Convert to E.164 format
                if not clean_phone.startswith('+'):
                    if clean_phone.startswith('91') and len(clean_phone) == 12:
                        clean_phone = '+' + clean_phone
                    elif len(clean_phone) == 10:
                        clean_phone = '+91' + clean_phone
                    elif clean_phone.startswith('0') and len(clean_phone) == 11:
                        clean_phone = '+91' + clean_phone[1:]
                
                # Update if changed
                if clean_phone != lead.phone and len(clean_phone) >= 13:
                    self.stdout.write(f"Fixing {lead.name}: {lead.phone} -> {clean_phone}")
                    lead.phone = clean_phone
                    lead.save()
                    fixed_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Fixed {fixed_count} phone numbers'))