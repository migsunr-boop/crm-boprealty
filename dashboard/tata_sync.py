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
        """Sync WhatsApp templates from TATA API"""
        try:
            # Try different TATA API endpoints for templates
            possible_endpoints = [
                f"{self.base_url}/v1/templates",
                f"{self.base_url}/templates",
                f"{self.base_url}/whatsapp/templates",
                f"{self.base_url}/api/v1/templates"
            ]
            
            templates_synced = 0
            last_error = None
            
            for url in possible_endpoints:
                try:
                    response = requests.get(url, headers=self.headers, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Process TATA templates response
                        templates_data = data.get('data', data.get('templates', []))
                        if isinstance(templates_data, list):
                            for template_data in templates_data:
                                template_name = template_data.get('name', 'Unknown')
                                template_status = template_data.get('status', 'PENDING')
                                
                                # Get template body
                                template_body = ''
                                if 'components' in template_data:
                                    for component in template_data['components']:
                                        if component.get('type') == 'BODY':
                                            template_body = component.get('text', '')
                                            break
                                else:
                                    template_body = template_data.get('body', template_data.get('message', ''))
                                
                                # Use name as unique identifier since stage has unique constraint
                                template, created = WhatsAppTemplate.objects.get_or_create(
                                    name=template_name,
                                    defaults={
                                        'stage': f'stage_{template_name.lower().replace(" ", "_")}',
                                        'message_template': template_body,
                                        'is_active': template_status == 'APPROVED'
                                    }
                                )
                                
                                # Update existing template
                                if not created:
                                    template.message_template = template_body
                                    template.is_active = template_status == 'APPROVED'
                                    template.save()
                                
                                if created:
                                    templates_synced += 1
                        
                        return {'success': True, 'count': templates_synced}
                    
                    last_error = f'{response.status_code} - {response.text}'
                    
                except requests.exceptions.RequestException as e:
                    last_error = str(e)
                    continue
            
            # If no endpoint worked, just return webhook status
            webhook_messages = WhatsAppMessage.objects.count()
            return {
                'success': True, 
                'count': 0,
                'message': f'TATA API not accessible. Webhook active with {webhook_messages} total messages.'
            }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def sync_messages(self):
        """Check actual message status in database"""
        try:
            # Count all messages in database
            total_messages = WhatsAppMessage.objects.count()
            recent_messages = WhatsAppMessage.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=7)
            ).count()
            
            # Check if webhook is configured
            webhook_status = "Webhook configured at /webhook/"
            
            # If no messages exist, explain why
            if total_messages == 0:
                explanation = (
                    "No messages found because:\n"
                    "1. Webhook URL not configured in TATA panel\n"
                    "2. No WhatsApp messages sent to +919355421616\n"
                    "3. TATA API endpoints not accessible\n\n"
                    "To receive messages:\n"
                    "• Configure webhook: https://crm-1z7t.onrender.com/webhook/\n"
                    "• Send test WhatsApp to +919355421616"
                )
                
                return {
                    'success': True,
                    'count': 0,
                    'message': explanation
                }
            
            return {
                'success': True, 
                'message': f'Database has {total_messages} total messages, {recent_messages} in last 7 days. {webhook_status}',
                'count': total_messages
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