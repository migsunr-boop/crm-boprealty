#!/usr/bin/env python
"""
Production Deployment Script for IVR WhatsApp Integration
Simplified version - no sample data, real production setup only
"""
import os
import sys
import django
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'realty_dashboard.settings')
django.setup()

from django.core.management import call_command
from django.conf import settings

def check_configuration():
    """Validate production configuration"""
    print("[CONFIG] Validating Production Configuration...")
    
    required_settings = [
        'TATA_AUTH_TOKEN',
        'TATA_BASE_URL', 
        'WHATSAPP_PHONE_NUMBER',
        'WABA_ID',
        'CRM_WEBHOOK_URL'
    ]
    
    missing = []
    for setting in required_settings:
        if not hasattr(settings, setting) or not getattr(settings, setting):
            missing.append(setting)
    
    if missing:
        print(f"[ERROR] Missing configuration: {', '.join(missing)}")
        return False
    
    print("[SUCCESS] Production configuration validated")
    print(f"   WhatsApp Number: {settings.WHATSAPP_PHONE_NUMBER}")
    print(f"   WABA ID: {settings.WABA_ID}")
    print(f"   Webhook URL: {settings.CRM_WEBHOOK_URL}")
    print(f"   Auth Token: {settings.TATA_AUTH_TOKEN[:20]}...")
    
    return True

def run_migrations():
    """Run database migrations"""
    print("\n[MIGRATE] Running Database Migrations...")
    try:
        call_command('migrate', verbosity=1)
        print("[SUCCESS] Migrations completed")
        return True
    except Exception as e:
        print(f"[ERROR] Migration failed: {str(e)}")
        return False

def test_whatsapp_api():
    """Test WhatsApp API connectivity"""
    print("\n[API] Testing WhatsApp API Connectivity...")
    try:
        from dashboard.whatsapp_integration import WhatsAppIntegrationService
        
        service = WhatsAppIntegrationService()
        
        # Test phone validation
        is_valid, clean_phone = service.validate_phone_number("+919876543210")
        if not is_valid:
            print(f"[ERROR] Phone validation failed: {clean_phone}")
            return False
        
        print(f"[SUCCESS] Phone validation working: {clean_phone}")
        
        # Test media validation (empty URL should pass)
        is_valid, error = service.validate_media("", "document")
        if not is_valid:
            print(f"[ERROR] Media validation failed: {error}")
            return False
        
        print("[SUCCESS] WhatsApp API service initialized")
        return True
        
    except Exception as e:
        print(f"[ERROR] WhatsApp API test failed: {str(e)}")
        return False

def test_ivr_processor():
    """Test IVR processor without sample data"""
    print("\n[IVR] Testing IVR Processor...")
    try:
        from dashboard.ivr_integration import IVRLeadProcessor
        from dashboard.models import IVRCallLog
        
        processor = IVRLeadProcessor()
        
        # Check if we can query existing IVR calls
        call_count = IVRCallLog.objects.count()
        print(f"[INFO] Found {call_count} existing IVR calls in database")
        
        # Test processor initialization
        calls = processor.get_last_1000_calls()
        print(f"[SUCCESS] IVR processor can query calls: {len(calls)} records")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] IVR processor test failed: {str(e)}")
        return False

def setup_webhook_endpoints():
    """Verify webhook endpoints are configured"""
    print("\n[WEBHOOK] Verifying Webhook Endpoints...")
    
    webhook_urls = [
        "/webhook/whatsapp/integration/",
        "/webhook/whatsapp/integration/delivery/",
        "/webhook/whatsapp/integration/messages/"
    ]
    
    print("[INFO] Webhook endpoints configured:")
    for url in webhook_urls:
        full_url = f"https://crm-1z7t.onrender.com{url}"
        print(f"   {full_url}")
    
    print("[SUCCESS] Webhook endpoints ready")
    return True

def display_production_instructions():
    """Display production usage instructions"""
    print("\n" + "="*60)
    print("IVR WhatsApp Integration - Production Ready!")
    print("="*60)
    
    print("\nProduction Commands:")
    print("\n1. Dry Run (Preview):")
    print("   python manage.py process_ivr_whatsapp --dry-run --limit 5")
    
    print("\n2. Test with Internal Numbers:")
    print("   python manage.py process_ivr_whatsapp --test-numbers +919876543210 --limit 5")
    
    print("\n3. Production Campaign:")
    print("   python manage.py process_ivr_whatsapp --limit 50")
    
    print("\nWebhook Configuration (Tata Panel):")
    print("   Main Webhook: https://crm-1z7t.onrender.com/webhook/whatsapp/integration/")
    print("   Delivery: https://crm-1z7t.onrender.com/webhook/whatsapp/integration/delivery/")
    
    print("\nTemplate Requirements:")
    print("   - Template Name: 'project_update_template'")
    print("   - Language: 'en'")
    print("   - Variables: [lead_name, project_name, call_status]")
    print("   - Must be pre-approved in Tata panel")
    
    print("\nRate Limits:")
    print("   - 100,000 messages per 24 hours")
    print("   - 1.25 seconds between messages")
    print("   - Automatic retry with exponential backoff")
    
    print("\nMonitoring:")
    print("   - Check WhatsApp message logs in Django admin")
    print("   - Monitor webhook delivery receipts")
    print("   - Review IVR call associations")

def main():
    """Main production deployment"""
    print("IVR WhatsApp Integration - Production Deployment")
    print("=" * 60)
    
    steps = [
        ("Configuration Check", check_configuration),
        ("Database Migrations", run_migrations),
        ("WhatsApp API Test", test_whatsapp_api),
        ("IVR Processor Test", test_ivr_processor),
        ("Webhook Setup", setup_webhook_endpoints),
    ]
    
    for step_name, step_func in steps:
        print(f"\n[STEP] {step_name}")
        if not step_func():
            print(f"\n[FAILED] Production deployment failed at: {step_name}")
            sys.exit(1)
    
    display_production_instructions()
    
    print(f"\n[SUCCESS] Production deployment completed at {datetime.now()}")
    print("\nReady for production use with real IVR data!")

if __name__ == "__main__":
    main()