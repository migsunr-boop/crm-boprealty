import requests
import json
from django.conf import settings
from django.utils import timezone
from .models import WhatsAppMessage, WhatsAppTemplate, Lead, LeadNote
from datetime import datetime, timedelta

class TATASync:
    def __init__(self):
        self.base_url = "https://wb.omni.tatatelebusiness.com"
        self.headers = {
            'Authorization': f'Bearer {settings.TATA_AUTH_TOKEN}',
            'Content-Type': 'application/json'
        }
    
    def sync_all_data(self):
        """Sync all data from TATA"""
        results = {
            'templates': self.sync_templates(),
            'messages': self.sync_messages(),
            'status': 'completed'
        }
        return results
    
    def sync_templates(self):
        """Create sample WhatsApp templates for real estate"""
        try:
            sample_templates = [
                {
                    'name': 'welcome_message',
                    'stage': 'stage_1_landing',
                    'message_template': 'Hello {name}, welcome to Bop Realty! We are excited to help you find your dream property.'
                },
                {
                    'name': 'property_inquiry',
                    'stage': 'stage_2_interested',
                    'message_template': 'Hi {name}, thank you for your interest in {project_name}. Our team will contact you shortly.'
                },
                {
                    'name': 'site_visit_reminder',
                    'stage': 'stage_5_site_visit',
                    'message_template': 'Hi {name}, reminder for your site visit to {project_name} on {date} at {time}.'
                }
            ]
            
            templates_synced = 0
            for template_data in sample_templates:
                template, created = WhatsAppTemplate.objects.get_or_create(
                    stage=template_data['stage'],
                    defaults={
                        'name': template_data['name'],
                        'message_template': template_data['message_template'],
                        'is_active': True
                    }
                )
                if created:
                    templates_synced += 1
            
            return {'success': True, 'count': templates_synced}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def sync_messages(self):
        """Sync messages from webhook data or conversation history"""
        # Since TATA doesn't provide a direct API to fetch all messages,
        # we'll work with the webhook data that's already being received
        try:
            # Get recent messages from our database to check sync status
            recent_messages = WhatsAppMessage.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=7)
            ).count()
            
            return {
                'success': True, 
                'message': f'Webhook active - {recent_messages} messages in last 7 days',
                'count': recent_messages
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_conversation_history(self, phone_number, limit=50):
        """Get conversation history for a specific phone number"""
        try:
            messages = WhatsAppMessage.objects.filter(
                phone_number=phone_number
            ).order_by('-created_at')[:limit]
            
            conversation_data = []
            for msg in messages:
                conversation_data.append({
                    'id': msg.message_id,
                    'phone_number': msg.phone_number,
                    'message': msg.message_content,
                    'timestamp': msg.created_at.isoformat(),
                    'status': msg.status,
                    'direction': 'inbound' if msg.status == 'received' else 'outbound'
                })
            
            return {'success': True, 'messages': conversation_data}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def send_template_message(self, to_number, template_name, language='en', components=None):
        """Send a template message via TATA API"""
        try:
            url = f"{self.base_url}/whatsapp-cloud/messages"
            
            payload = {
                "to": to_number,
                "type": "template",
                "source": "crm",
                "template": {
                    "name": template_name,
                    "language": {
                        "code": language
                    },
                    "components": components or []
                }
            }
            
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                message_id = result.get('id')
                
                # Find or create lead for this phone number
                lead = Lead.objects.filter(phone=to_number).first()
                if not lead:
                    lead = Lead.objects.create(
                        name=f"WhatsApp Lead {to_number}",
                        phone=to_number,
                        email=f"{to_number}@whatsapp.temp",
                        source='whatsapp'
                    )
                
                # Save to database
                WhatsAppMessage.objects.create(
                    lead=lead,
                    phone_number=to_number,
                    message_content=f"Template: {template_name}",
                    message_id=message_id,
                    status='sent'
                )
                
                return {'success': True, 'message_id': message_id}
            else:
                return {'success': False, 'error': f'API Error: {response.status_code}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def send_session_message(self, to_number, message_text):
        """Send a session message via TATA API"""
        try:
            url = f"{self.base_url}/whatsapp-cloud/messages"
            
            payload = {
                "to": to_number,
                "type": "text",
                "source": "crm",
                "text": {
                    "body": message_text
                }
            }
            
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                message_id = result.get('id')
                
                # Find or create lead for this phone number
                lead = Lead.objects.filter(phone=to_number).first()
                if not lead:
                    lead = Lead.objects.create(
                        name=f"WhatsApp Lead {to_number}",
                        phone=to_number,
                        email=f"{to_number}@whatsapp.temp",
                        source='whatsapp'
                    )
                
                # Save to database
                WhatsAppMessage.objects.create(
                    lead=lead,
                    phone_number=to_number,
                    message_content=message_text,
                    message_id=message_id,
                    status='sent'
                )
                
                return {'success': True, 'message_id': message_id}
            else:
                return {'success': False, 'error': f'API Error: {response.status_code}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_all_conversations(self):
        """Get all unique conversations from database"""
        try:
            # Get unique phone numbers with their latest message
            conversations = []
            unique_numbers = WhatsAppMessage.objects.values('phone_number').distinct()
            
            for number_data in unique_numbers:
                phone_number = number_data['phone_number']
                latest_message = WhatsAppMessage.objects.filter(
                    phone_number=phone_number
                ).order_by('-created_at').first()
                
                if latest_message:
                    # Get lead info if exists
                    lead = Lead.objects.filter(phone=phone_number).first()
                    
                    conversations.append({
                        'phone_number': phone_number,
                        'latest_message': latest_message.message_content,
                        'latest_time': latest_message.created_at.isoformat(),
                        'status': latest_message.status,
                        'lead_name': lead.name if lead else 'Unknown',
                        'lead_id': lead.id if lead else None
                    })
            
            # Sort by latest message time
            conversations.sort(key=lambda x: x['latest_time'], reverse=True)
            
            return {'success': True, 'conversations': conversations}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}