#!/usr/bin/env python
"""
Test WhatsApp campaign with real leads
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'realty_dashboard.settings')
django.setup()

from dashboard.tata_whatsapp_service import TataWhatsAppCampaignService

def run_test_campaign():
    print("Testing WhatsApp Campaign with Real Leads")
    print("=" * 50)
    
    campaign_service = TataWhatsAppCampaignService()
    
    # Test with last 365 days (broader range)
    from django.utils import timezone
    to_date = timezone.now()
    from_date = to_date - timedelta(days=365)
    
    print(f"Date range: {from_date.date()} to {to_date.date()}")
    
    # Run dry campaign
    results = campaign_service.run_campaign(
        project_names=[],  # All projects
        from_date=from_date,
        to_date=to_date,
        template_name="test_template",
        language="en",
        dry_run=True,  # DRY RUN ONLY
        limit=10
    )
    
    print(f"\nResults:")
    print(f"Total Leads: {results['total_leads']}")
    print(f"Valid Leads: {results['valid_leads']}")
    print(f"Would Send: {results['sent_count']}")
    print(f"Errors: {len(results['errors'])}")
    
    if results['sent_messages']:
        print(f"\nSample leads that would receive messages:")
        for msg in results['sent_messages'][:5]:
            print(f"- {msg['lead_name']}: {msg['phone']}")
    
    if results['errors']:
        print(f"\nErrors:")
        for error in results['errors'][:3]:
            print(f"- {error}")

if __name__ == "__main__":
    run_test_campaign()