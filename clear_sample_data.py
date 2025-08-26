#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'realty_dashboard.settings')
django.setup()

from dashboard.models import WhatsAppMessage, WhatsAppTemplate, Lead

# Delete sample data
print("Deleting sample WhatsApp messages...")
WhatsAppMessage.objects.filter(phone_number__in=['+919876543210', '+919876543211', '+919876543212']).delete()

print("Deleting sample leads...")
Lead.objects.filter(phone__in=['+919876543210', '+919876543211', '+919876543212']).delete()

print("Deleting sample templates...")
WhatsAppTemplate.objects.filter(name__in=['welcome_message', 'property_inquiry', 'site_visit_reminder']).delete()

print("Sample data cleared!")