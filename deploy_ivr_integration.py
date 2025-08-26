#!/usr/bin/env python
"""
Deployment Script for IVR WhatsApp Integration
Sets up database, runs tests, and validates configuration
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
    """Validate configuration settings"""
    print("[CONFIG] Checking Configuration...")
    
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
    
    print("[SUCCESS] Configuration validated")
    
    # Display key settings (masked)
    print(f"   WhatsApp Number: {settings.WHATSAPP_PHONE_NUMBER}")
    print(f"   WABA ID: {settings.WABA_ID}")
    print(f"   Webhook URL: {settings.CRM_WEBHOOK_URL}")
    print(f"   Auth Token: {settings.TATA_AUTH_TOKEN[:20]}...")
    
    return True

def run_migrations():
    """Run database migrations"""
    print("\n[MIGRATE] Running Database Migrations...")
    try:
        call_command('makemigrations', verbosity=1)
        call_command('migrate', verbosity=1)
        print("[SUCCESS] Migrations completed")
        return True
    except Exception as e:
        print(f"[ERROR] Migration failed: {str(e)}")
        return False

def test_integration():
    """Run integration tests"""
    print("\n[TEST] Running Integration Tests...")
    try:
        # Import and run test
        from test_ivr_integration import run_acceptance_tests
        run_acceptance_tests()
        return True
    except Exception as e:
        print(f"[ERROR] Tests failed: {str(e)}")
        return False

def create_sample_data():
    """Create sample data for testing"""
    print("\n[DATA] Creating Sample Data...")
    try:
        from test_ivr_integration import create_sample_ivr_data
        create_sample_ivr_data()
        print("[SUCCESS] Sample data created")
        return True
    except Exception as e:
        print(f"[ERROR] Sample data creation failed: {str(e)}")
        return False

def test_dry_run():
    """Test dry run of IVR processing"""
    print("\n[DRYRUN] Testing Dry Run...")
    try:
        call_command('process_ivr_whatsapp', '--dry-run', '--limit', '3', verbosity=1)
        print("[SUCCESS] Dry run completed")
        return True
    except Exception as e:
        print(f"[ERROR] Dry run failed: {str(e)}")
        return False

def display_usage_instructions():
    """Display usage instructions"""
    print("\n" + "="*60)
    print("IVR WhatsApp Integration - Deployment Complete!")
    print("="*60)
    
    print("\nUsage Instructions:")
    print("\n1. Preview Campaign (Dry Run):")
    print("   python manage.py process_ivr_whatsapp --dry-run --limit 5")
    
    print("\n2. Test with Internal Numbers:")
    print("   python manage.py process_ivr_whatsapp --test-numbers +919876543210 --limit 5")
    
    print("\n3. Run Live Campaign:")
    print("   python manage.py process_ivr_whatsapp --limit 10")
    
    print("\n4. Monitor Results:")
    print("   - Check WhatsApp message logs in Django admin")
    print("   - Monitor webhook delivery receipts")
    print("   - Review campaign analytics")
    
    print("\nImportant Notes:")
    print("   - Ensure template 'project_update_template' exists in Tata panel")
    print("   - Webhook URL configured: https://crm-1z7t.onrender.com/webhook/whatsapp/integration/")
    print("   - Rate limit: 1.25 seconds between messages (100k/24h)")
    print("   - Media validation: PDF <100MB, Images <5MB")
    
    print("\nWebhook Endpoints:")
    print("   - Main: /webhook/whatsapp/integration/")
    print("   - Delivery: /webhook/whatsapp/integration/delivery/")
    print("   - Messages: /webhook/whatsapp/integration/messages/")
    
    print("\nSupport:")
    print("   - Check logs for errors")
    print("   - Validate phone numbers in E.164 format")
    print("   - Ensure templates are approved in Tata panel")

def main():
    """Main deployment function"""
    print("Starting IVR WhatsApp Integration Deployment")
    print("=" * 60)
    
    steps = [
        ("Configuration Check", check_configuration),
        ("Database Migrations", run_migrations),
        ("Sample Data Creation", create_sample_data),
        ("Integration Tests", test_integration),
        ("Dry Run Test", test_dry_run),
    ]
    
    for step_name, step_func in steps:
        print(f"\n[STEP] {step_name}")
        if not step_func():
            print(f"\n[FAILED] Deployment failed at: {step_name}")
            sys.exit(1)
    
    display_usage_instructions()
    
    print(f"\n[SUCCESS] Deployment completed successfully at {datetime.now()}")

if __name__ == "__main__":
    main()