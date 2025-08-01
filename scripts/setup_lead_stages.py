#!/usr/bin/env python
"""
Script to set up default lead stages for the CRM system
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'realty_dashboard.settings')
django.setup()

from dashboard.models import LeadStage

def create_default_stages():
    """Create default lead stages"""
    
    default_stages = [
        # New Leads
        {'name': 'Fresh Lead', 'category': 'new', 'order': 1, 'color': '#3b82f6', 'description': 'Newly captured lead'},
        {'name': 'Initial Contact', 'category': 'new', 'order': 2, 'color': '#06b6d4', 'description': 'First contact attempted'},
        
        # Warm Leads
        {'name': 'Interested', 'category': 'warm', 'order': 3, 'color': '#f59e0b', 'description': 'Showed interest in properties'},
        {'name': 'Follow-up Required', 'category': 'warm', 'order': 4, 'color': '#f97316', 'description': 'Needs regular follow-up'},
        {'name': 'Site Visit Scheduled', 'category': 'warm', 'order': 5, 'color': '#eab308', 'description': 'Site visit appointment set'},
        
        # Hot Leads
        {'name': 'Site Visit Done', 'category': 'hot', 'order': 6, 'color': '#ef4444', 'description': 'Completed site visit'},
        {'name': 'Negotiation', 'category': 'hot', 'order': 7, 'color': '#dc2626', 'description': 'Price negotiation in progress'},
        {'name': 'Ready to Close', 'category': 'hot', 'order': 8, 'color': '#b91c1c', 'description': 'Ready for final closure'},
        
        # Cold Leads
        {'name': 'Not Interested', 'category': 'cold', 'order': 9, 'color': '#6b7280', 'description': 'Currently not interested'},
        {'name': 'Budget Mismatch', 'category': 'cold', 'order': 10, 'color': '#4b5563', 'description': 'Budget does not match'},
        {'name': 'Future Prospect', 'category': 'cold', 'order': 11, 'color': '#374151', 'description': 'May be interested in future'},
        
        # Closed Leads
        {'name': 'Deal Closed', 'category': 'closed', 'order': 12, 'color': '#10b981', 'description': 'Successfully converted to customer'},
        {'name': 'Lost to Competitor', 'category': 'closed', 'order': 13, 'color': '#ef4444', 'description': 'Lost to competitor'},
        
        # Dead Leads
        {'name': 'Invalid Number', 'category': 'dead', 'order': 14, 'color': '#1f2937', 'description': 'Phone number is invalid'},
        {'name': 'Duplicate Lead', 'category': 'dead', 'order': 15, 'color': '#111827', 'description': 'Duplicate entry'},
        {'name': 'Spam/Junk', 'category': 'dead', 'order': 16, 'color': '#000000', 'description': 'Spam or junk lead'},
    ]
    
    created_count = 0
    
    for stage_data in default_stages:
        stage, created = LeadStage.objects.get_or_create(
            name=stage_data['name'],
            defaults={
                'category': stage_data['category'],
                'order': stage_data['order'],
                'color': stage_data['color'],
                'description': stage_data['description'],
                'is_active': True
            }
        )
        
        if created:
            created_count += 1
            print(f"✅ Created stage: {stage.name} ({stage.category})")
        else:
            print(f"⚠️  Stage already exists: {stage.name}")
    
    print(f"\n🎉 Setup complete! Created {created_count} new lead stages.")
    print(f"📊 Total stages in system: {LeadStage.objects.count()}")

def create_default_whatsapp_templates():
    """Create default WhatsApp templates"""
    from dashboard.models import WhatsAppTemplate
    
    templates = [
        {
            'name': 'Call Landing Response',
            'stage': 'stage_1_landing',
            'message_template': 'Hi {name}! Thank you for your interest in {project_name}. Our team will call you shortly to discuss the details. For immediate assistance, call {number}.'
        },
        {
            'name': 'Interested Follow-up',
            'stage': 'stage_2_interested',
            'message_template': 'Hello {name}! Thank you for showing interest in {project_name}. We have some exciting offers for you. When would be a good time to schedule a site visit?'
        },
        {
            'name': 'Not Picking Up',
            'stage': 'stage_3_not_picking',
            'message_template': 'Hi {name}, We tried calling you regarding {project_name} but couldn\'t connect. Please let us know your preferred time to call. WhatsApp us at {number}.'
        },
        {
            'name': 'Missed IVR Call',
            'stage': 'stage_4_missed_ivr',
            'message_template': 'Hi {name}! We received your missed call regarding {project_name}. Our executive will call you back shortly. For immediate assistance: {number}'
        },
        {
            'name': 'Site Visit Reminder',
            'stage': 'stage_5_site_visit',
            'message_template': 'Hi {name}! This is a reminder for your site visit to {project_name} tomorrow. Looking forward to meeting you! Contact: {number}'
        },
        {
            'name': '7 Day Follow-up',
            'stage': 'stage_6_day_7',
            'message_template': 'Hi {name}! Hope you liked {project_name} during your visit. We have some special offers this week. Interested to know more? Call {number}'
        },
        {
            'name': '15 Day Follow-up',
            'stage': 'stage_7_day_15',
            'message_template': 'Hello {name}! Still thinking about {project_name}? We have limited units left with attractive payment plans. Let\'s discuss: {number}'
        },
        {
            'name': '30 Day Follow-up',
            'stage': 'stage_8_day_30',
            'message_template': 'Hi {name}! Last chance to book your dream home at {project_name} with our special pricing. Units are selling fast! Call now: {number}'
        }
    ]
    
    created_count = 0
    
    for template_data in templates:
        template, created = WhatsAppTemplate.objects.get_or_create(
            stage=template_data['stage'],
            defaults={
                'name': template_data['name'],
                'message_template': template_data['message_template'],
                'is_active': True
            }
        )
        
        if created:
            created_count += 1
            print(f"✅ Created WhatsApp template: {template.name}")
        else:
            print(f"⚠️  Template already exists: {template.name}")
    
    print(f"\n📱 WhatsApp templates setup complete! Created {created_count} new templates.")

if __name__ == '__main__':
    print("🚀 Setting up default lead stages and WhatsApp templates...")
    print("=" * 60)
    
    create_default_stages()
    print("\n" + "=" * 60)
    create_default_whatsapp_templates()
    
    print("\n✨ All setup tasks completed successfully!")
    print("🎯 Your CRM system is now ready to use!")
