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
        """Fetch and sync WhatsApp templates"""
        try:
            # Get template insights to fetch template data
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            url = f"{self.base_url}/templates/insights"
            params = {
                'startDate': start_date,
                'endDate': end_date,
                'granularity': 'DAILY',
                'templateIDs': 'all'  # This might need adjustment based on actual API
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                templates_synced = 0
                
                # Process template data
                if 'data' in data and 'data_points' in data['data']:
                    for template_data in data['data']['data_points']:
                        template_id = template_data.get('template_id')
                        if template_id:
                            # Create or update template
                            template, created = WhatsAppTemplate.objects.get_or_create(
                                template_id=template_id,
                                defaults={
                                    'name': f'Template_{template_id}',
                                    'language': 'en',
                                    'category': 'MARKETING',
                                    'status': 'APPROVED',
                                    'created_at': timezone.now()
                                }
                            )
                            templates_synced += 1
                
                return {'success': True, 'count': templates_synced}
            else:
                return {'success': False, 'error': f'API Error: {response.status_code}'}
                
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
                
                # Save to database
                WhatsAppMessage.objects.create(
                    phone_number=to_number,
                    message_content=f"Template: {template_name}",
                    message_id=message_id,
                    status='sent',
                    created_at=timezone.now()
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
                
                # Save to database
                WhatsAppMessage.objects.create(
                    phone_number=to_number,
                    message_content=message_text,
                    message_id=message_id,
                    status='sent',
                    created_at=timezone.now()
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