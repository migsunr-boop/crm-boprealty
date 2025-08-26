"""
IVR WhatsApp Campaign - Send templates to today's leads
"""
import hashlib
import hmac
import time
import requests
from datetime import datetime
from django.utils import timezone
from django.conf import settings
from .models import Lead

class IVRWhatsAppCampaign:
    
    def __init__(self):
        self.webhook_url = "https://crm-boprealty.onrender.com/webhook/whatsapp/integration/"
        self.secret_key = getattr(settings, 'SECRET_KEY', 'default-secret')
    
    def send_to_todays_leads(self):
        """Send WhatsApp templates to today's IVR leads"""
        
        # Get today's IVR leads that haven't received WhatsApp
        today = timezone.now().date()
        leads_to_message = Lead.objects.filter(
            source='ivr_call',
            created_at__date=today
        ).exclude(
            whatsapp_messages__sent_at__date=today
        )
        
        results = {
            'total_leads': leads_to_message.count(),
            'sent_successfully': 0,
            'failed': 0,
            'errors': []
        }
        
        for lead in leads_to_message:
            try:
                # Generate security token
                timestamp = int(time.time())
                token_string = f"{lead.id}:{timestamp}"
                hash_value = hmac.new(
                    self.secret_key.encode(),
                    token_string.encode(),
                    hashlib.sha256
                ).hexdigest()[:12]
                token = f"{lead.id}:{timestamp}:{hash_value}"
                
                # Get project name
                project_name = "Real Estate Property"
                if lead.interested_projects.exists():
                    project_name = lead.interested_projects.first().name
                
                # Build template payload
                payload = {
                    "name": "project_update_template",
                    "language": "en",
                    "components": [
                        {
                            "type": "BODY",
                            "text": f"Hello {lead.name},\\nThank you for showing interest in {project_name}.\\nWe tried reaching you on a recent call regarding your inquiry.\\nWould you like to explore available options? Your last status was: New Lead."
                        },
                        {
                            "type": "FOOTER", 
                            "text": "Reply STOP to unsubscribe"
                        },
                        {
                            "type": "BUTTONS",
                            "buttons": [
                                {
                                    "type": "URL",
                                    "text": "Interested ✅",
                                    "url": f"https://crm-boprealty.onrender.com/tata-calls/{lead.id}?token={token}&action=interested"
                                },
                                {
                                    "type": "URL", 
                                    "text": "Not Interested ❌",
                                    "url": f"https://crm-boprealty.onrender.com/tata-calls/{lead.id}?token={token}&action=not_interested"
                                }
                            ]
                        }
                    ],
                    "phone": lead.phone,
                    "lead_id": lead.id
                }
                
                # Send to webhook
                response = requests.post(
                    self.webhook_url,
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                )
                
                if response.status_code == 200:
                    # Mark as sent
                    from .models import WhatsAppMessage
                    WhatsAppMessage.objects.create(
                        lead=lead,
                        message_content=f"Template sent to {lead.phone}",
                        phone_number=lead.phone,
                        status='sent',
                        sent_at=timezone.now()
                    )
                    results['sent_successfully'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append(f"Lead {lead.id}: HTTP {response.status_code}")
                    
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"Lead {lead.id}: {str(e)}")
        
        return results