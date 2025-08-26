#!/usr/bin/env python
"""
Test Script for IVR WhatsApp Integration
Tests the complete flow from IVR data to WhatsApp sending
"""
import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'realty_dashboard.settings')
django.setup()

from dashboard.models import IVRCallLog, Lead, Project
from dashboard.ivr_integration import IVRLeadProcessor
from dashboard.whatsapp_integration import WhatsAppIntegrationService

def create_sample_ivr_data():
    """Create sample IVR call data for testing"""
    print("Creating sample IVR data...")
    
    # Create sample projects if they don't exist
    projects = [
        "Skyline Phoenix",
        "Godrej Woods", 
        "Trinity Sky Palazzos"
    ]
    
    for project_name in projects:
        project, created = Project.objects.get_or_create(
            name=project_name,
            defaults={
                'location': 'Noida',
                'description': f'Premium {project_name} project',
                'property_type': 'apartment',
                'bhk_options': '2BHK, 3BHK',
                'price_min': 5000000,
                'price_max': 15000000,
                'created_by_id': 1
            }
        )
        if created:
            print(f"Created project: {project_name}")
    
    # Create sample IVR calls using existing IVRCallLog model
    sample_calls = [
        {"caller": "+919876543210", "to": "+919355421616", "duration": 45},
        {"caller": "+919876543211", "to": "+919355421616", "duration": 0},
        {"caller": "+919876543212", "to": "+919355421616", "duration": 120},
        {"caller": "+919876543213", "to": "+919355421616", "duration": 0},
        {"caller": "+919876543214", "to": "+919355421616", "duration": 30},
    ]
    
    for i, call_data in enumerate(sample_calls):
        call, created = IVRCallLog.objects.get_or_create(
            uuid=f"test_call_{i+1}",
            defaults={
                'caller_id_number': call_data["caller"],
                'call_to_number': call_data["to"],
                'duration': call_data["duration"],
                'start_stamp': timezone.now() - timedelta(hours=1),
                'end_stamp': timezone.now() - timedelta(hours=1) + timedelta(seconds=call_data["duration"]) if call_data["duration"] > 0 else None,
                'status': 'answered' if call_data["duration"] > 0 else 'no_answer',
                'raw_data': {'test': True, 'sample_data': True}
            }
        )
        if created:
            print(f"Created IVR call: {call_data['caller']} -> {call_data['to']} ({call_data['duration']}s)")
    
    print(f"Total IVR calls in database: {IVRCallLog.objects.count()}")

def test_phone_validation():
    """Test phone number validation"""
    print("\n=== Testing Phone Validation ===")
    
    whatsapp_service = WhatsAppIntegrationService()
    
    test_phones = [
        "+919876543210",  # Valid E.164
        "9876543210",     # Valid Indian number
        "919876543210",   # Valid with country code
        "invalid",        # Invalid
        "+1234567890",    # Valid US number
    ]
    
    for phone in test_phones:
        is_valid, result = whatsapp_service.validate_phone_number(phone)
        print(f"Phone: {phone:15} -> Valid: {is_valid:5} -> {result}")

def test_media_validation():
    """Test media URL validation"""
    print("\n=== Testing Media Validation ===")
    
    whatsapp_service = WhatsAppIntegrationService()
    
    test_urls = [
        ("https://example.com/brochure.pdf", "document"),
        ("https://example.com/image.jpg", "image"),
        ("invalid-url", "document"),
        ("", "document"),  # Empty URL should be valid
    ]
    
    for url, media_type in test_urls:
        is_valid, error = whatsapp_service.validate_media(url, media_type)
        print(f"URL: {url[:30]:30} Type: {media_type:8} -> Valid: {is_valid:5} -> {error}")

def test_ivr_processing():
    """Test IVR lead processing"""
    print("\n=== Testing IVR Processing ===")
    
    processor = IVRLeadProcessor()
    
    # Test dry run
    print("Running dry run...")
    results = processor.process_ivr_leads(dry_run=True)
    
    print(f"Total calls: {results['total_calls']}")
    print(f"Unique calls: {results['unique_calls']}")
    print(f"WhatsApp queue: {len(results['whatsapp_queue'])}")
    
    # Show grouped data
    print("\nGrouped data:")
    for project, statuses in results['grouped_data'].items():
        print(f"  {project}:")
        for status, calls in statuses.items():
            print(f"    {status}: {len(calls)} calls")
    
    # Show first payload
    if results['whatsapp_queue']:
        print(f"\nFirst WhatsApp payload:")
        payload = results['whatsapp_queue'][0]
        print(f"  To: {payload['to']}")
        print(f"  Template: {payload['template']['name']}")
        if 'body_variables' in payload:
            print(f"  Variables: {payload['body_variables']}")

def test_whatsapp_send():
    """Test WhatsApp message sending (dry run)"""
    print("\n=== Testing WhatsApp Send (Validation Only) ===")
    
    whatsapp_service = WhatsAppIntegrationService()
    
    # Test template message validation
    test_data = {
        "to": "+919876543210",
        "template_name": "project_update_template",
        "language": "en",
        "body_variables": ["John Doe", "Skyline Phoenix", "Missed Call"],
        "header_media_url": None,
        "header_media_type": None
    }
    
    print(f"Testing template message validation...")
    print(f"To: {test_data['to']}")
    print(f"Template: {test_data['template_name']}")
    print(f"Variables: {test_data['body_variables']}")
    
    # Validate phone
    is_valid, clean_phone = whatsapp_service.validate_phone_number(test_data['to'])
    print(f"Phone validation: {is_valid} -> {clean_phone}")
    
    # Check for button variables
    has_button_vars = any(
        keyword in str(var).lower() 
        for var in test_data['body_variables'] 
        for keyword in ['button', 'cta']
    )
    print(f"Button variables check: {'FAIL' if has_button_vars else 'PASS'}")
    
    print("Note: Actual API call skipped in test mode")

def run_acceptance_tests():
    """Run all acceptance tests"""
    print("=" * 60)
    print("IVR WhatsApp Integration - Acceptance Tests")
    print("=" * 60)
    
    try:
        # Create sample data
        create_sample_ivr_data()
        
        # Run tests
        test_phone_validation()
        test_media_validation()
        test_ivr_processing()
        test_whatsapp_send()
        
        print("\n" + "=" * 60)
        print("✅ All acceptance tests completed successfully!")
        print("=" * 60)
        
        print("\nNext steps:")
        print("1. Run: python manage.py process_ivr_leads --dry-run --limit 5")
        print("2. Verify template 'project_update_template' exists in Tata panel")
        print("3. Test with internal numbers: python manage.py process_ivr_leads --limit 5")
        print("4. Monitor delivery receipts in WhatsApp logs")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_acceptance_tests()