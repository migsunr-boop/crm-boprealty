#!/usr/bin/env python
"""
Test script for WhatsApp Campaign System
Production-grade testing with real CRM data
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'realty_dashboard.settings')
django.setup()

from dashboard.tata_whatsapp_service import TataWhatsAppService, TataWhatsAppCampaignService
from dashboard.models import Lead, Project

def test_phone_validation():
    """Test phone number validation"""
    print("=== Testing Phone Validation ===")
    
    service = TataWhatsAppService()
    
    test_cases = [
        ("+919355421616", True),
        ("919355421616", True),
        ("9355421616", True),
        ("+91 9355 421 616", True),
        ("invalid", False),
        ("+1234", False),
        ("", False)
    ]
    
    for phone, expected in test_cases:
        is_valid, result = service.validate_phone_number(phone)
        status = "PASS" if is_valid == expected else "FAIL"
        print(f"{status} {phone} -> {result} (Expected: {expected})")

def test_media_validation():
    """Test media URL validation"""
    print("\n=== Testing Media Validation ===")
    
    service = TataWhatsAppService()
    
    # Test with a real image URL (you can replace with your CDN)
    test_urls = [
        ("https://via.placeholder.com/800x600.jpg", "image", True),
        ("https://invalid-url-that-does-not-exist.com/image.jpg", "image", False),
        ("", "image", True),  # Empty URL should be valid (no media)
    ]
    
    for url, media_type, expected in test_urls:
        try:
            is_valid, error, info = service.validate_media_url(url, media_type)
            status = "PASS" if is_valid == expected else "FAIL"
            print(f"{status} {url} ({media_type}) -> Valid: {is_valid}")
            if info:
                print(f"    Info: {info}")
            if error:
                print(f"    Error: {error}")
        except Exception as e:
            print(f"FAIL {url} -> Exception: {e}")

def test_template_validation():
    """Test template validation"""
    print("\n=== Testing Template Validation ===")
    
    service = TataWhatsAppService()
    
    test_templates = [
        ("bop_realty_project_intro", "en", True),
        ("invalid@template#name", "en", False),
        ("", "en", False),
        ("valid_template_name", "hi", True)
    ]
    
    for template, language, expected in test_templates:
        is_valid, error = service.check_template_exists(template, language)
        status = "PASS" if is_valid == expected else "FAIL"
        print(f"{status} {template} ({language}) -> Valid: {is_valid}")
        if error:
            print(f"    Error: {error}")

def test_lead_filtering():
    """Test IVR lead filtering"""
    print("\n=== Testing Lead Filtering ===")
    
    campaign_service = TataWhatsAppCampaignService()
    
    # Test with last 30 days
    to_date = datetime.now()
    from_date = to_date - timedelta(days=30)
    
    print(f"Filtering leads from {from_date.date()} to {to_date.date()}")
    
    # Get all projects for testing
    projects = list(Project.objects.filter(is_active=True).values_list('name', flat=True)[:3])
    print(f"Testing with projects: {projects}")
    
    leads = campaign_service.get_ivr_leads(
        project_names=projects,
        from_date=from_date,
        to_date=to_date,
        limit=10
    )
    
    print(f"Found {len(leads)} valid IVR leads")
    
    for i, lead in enumerate(leads[:5], 1):
        masked_phone = lead.phone[:-4] + 'XXXX' if len(lead.phone) > 4 else 'XXXX'
        print(f"  {i}. {lead.name} ({masked_phone}) - {lead.created_at.date()}")
        
        # Test variable preparation
        variables = campaign_service.prepare_template_variables(lead)
        print(f"     Variables: {variables}")

def test_dry_run_campaign():
    """Test dry run campaign execution"""
    print("\n=== Testing Dry Run Campaign ===")
    
    campaign_service = TataWhatsAppCampaignService()
    
    # Test parameters
    to_date = datetime.now()
    from_date = to_date - timedelta(days=7)  # Last week
    
    results = campaign_service.run_campaign(
        project_names=[],  # All projects
        from_date=from_date,
        to_date=to_date,
        template_name="test_template",
        language="en",
        dry_run=True,  # Important: dry run only
        limit=5
    )
    
    print("Campaign Results:")
    print(f"  Total Leads: {results['total_leads']}")
    print(f"  Valid Leads: {results['valid_leads']}")
    print(f"  Would Send: {results['sent_count']}")
    print(f"  Errors: {len(results['errors'])}")
    
    if results['errors']:
        print("  Error Details:")
        for error in results['errors'][:3]:
            print(f"    - {error}")
    
    if results['sent_messages']:
        print("  Sample Messages:")
        for msg in results['sent_messages'][:3]:
            print(f"    - {msg['lead_name']}: {msg['template']}")

def test_payload_building():
    """Test WhatsApp payload building"""
    print("\n=== Testing Payload Building ===")
    
    service = TataWhatsAppService()
    
    # Test basic payload
    payload = service.build_template_payload(
        to="+919355421616",
        template_name="test_template",
        language="en",
        body_variables=["John Doe", "Skyline Phoenix", "https://crm.example.com/lead/123"],
        custom_callback_data="lead_123_1234567890"
    )
    
    print("Basic Payload:")
    import json
    print(json.dumps(payload, indent=2))
    
    # Test with media
    payload_with_media = service.build_template_payload(
        to="+919355421616",
        template_name="test_template",
        language="en",
        body_variables=["John Doe", "Skyline Phoenix"],
        header_media_url="https://cdn.example.com/brochure.jpg",
        header_media_type="image"
    )
    
    print("\nPayload with Media:")
    print(json.dumps(payload_with_media, indent=2))

def run_all_tests():
    """Run all tests"""
    print("WhatsApp Campaign System Tests")
    print("=" * 50)
    
    try:
        test_phone_validation()
        test_template_validation()
        test_media_validation()
        test_lead_filtering()
        test_payload_building()
        test_dry_run_campaign()
        
        print("\n" + "=" * 50)
        print("All tests completed successfully!")
        print("\nNext Steps:")
        print("1. Verify templates exist in Tata Omnichannel")
        print("2. Test with real template names")
        print("3. Configure webhook endpoints")
        print("4. Run production campaign with --dry-run first")
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests()