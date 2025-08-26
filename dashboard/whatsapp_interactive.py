"""
WhatsApp Interactive Templates with Secure Tracking
Generates CTA buttons with tokenized URLs for lead engagement tracking
"""
import hmac
import hashlib
import time
from typing import Dict, List, Tuple
from django.conf import settings
from django.utils import timezone
from .models import Lead, WhatsAppMessage
from .whatsapp_integration import WhatsAppIntegrationService

class WhatsAppInteractiveService:
    """Service for interactive WhatsApp templates with CTA buttons"""
    
    def __init__(self):
        self.whatsapp_service = WhatsAppIntegrationService()
        self.secret_key = getattr(settings, 'SECRET_KEY', 'fallback-secret')
        self.base_url = getattr(settings, 'CRM_WEBHOOK_URL', 'https://crm-1z7t.onrender.com')
    
    def generate_secure_token(self, lead_id: int) -> str:
        """Generate secure token for lead tracking"""
        timestamp = str(int(time.time()))
        payload = f"{lead_id}:{timestamp}"
        
        signature = hmac.new(
            self.secret_key.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()[:12]
        
        return f"{lead_id}:{timestamp}:{signature}"
    
    def validate_token(self, token: str, lead_id: int) -> bool:
        """Validate secure token"""
        try:
            token_lead_id, timestamp, signature = token.split(":")
            
            if str(lead_id) != token_lead_id:
                return False
            
            payload = f"{lead_id}:{timestamp}"
            expected_signature = hmac.new(
                self.secret_key.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()[:12]
            
            return hmac.compare_digest(expected_signature, signature)
        except Exception:
            return False
    
    def build_interactive_template(self, lead: Lead, project_name: str) -> Dict:
        """Build interactive WhatsApp template with CTA buttons"""
        
        token = self.generate_secure_token(lead.id)
        
        template = {
            "name": "project_update_template",
            "language": {"code": "en"},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": lead.name},
                        {"type": "text", "text": project_name}
                    ]
                },
                {
                    "type": "footer",
                    "text": "Bop Realty"
                },
                {
                    "type": "buttons",
                    "buttons": [
                        {
                            "type": "url",
                            "text": "Interested ✅",
                            "url": f"{self.base_url}/track/{lead.id}/?token={token}&action=interested"
                        },
                        {
                            "type": "url", 
                            "text": "Not Interested ❌",
                            "url": f"{self.base_url}/track/{lead.id}/?token={token}&action=not_interested"
                        }
                    ]
                }
            ]
        }
        
        return template
    
    def send_interactive_message(self, lead: Lead, project_name: str) -> Tuple[bool, str, Dict]:
        """Send interactive WhatsApp message with CTA buttons"""
        
        # Validate phone
        is_valid, clean_phone = self.whatsapp_service.validate_phone_number(lead.phone)
        if not is_valid:
            return False, clean_phone, {}
        
        # Build interactive template
        template = self.build_interactive_template(lead, project_name)
        
        # Send via WhatsApp API
        success, message_id, response = self.whatsapp_service.send_template_message(
            to=clean_phone,
            template_name=template["name"],
            language=template["language"]["code"],
            body_variables=[lead.name, project_name],
            lead_id=lead.id
        )
        
        # Log interactive message
        if success:
            WhatsAppMessage.objects.create(
                lead=lead,
                message_content=f"Interactive template: {project_name} with CTA buttons",
                phone_number=clean_phone,
                status='sent',
                message_id=message_id,
                api_response=response,
                sent_at=timezone.now()
            )
        
        return success, message_id, response
    
    def process_lead_response(self, lead_id: int, action: str, token: str) -> Dict:
        """Process lead response from CTA button click"""
        
        try:
            lead = Lead.objects.get(id=lead_id)
        except Lead.DoesNotExist:
            return {"status": "error", "message": "Lead not found"}
        
        # Validate token
        if not self.validate_token(token, lead_id):
            return {"status": "error", "message": "Invalid token"}
        
        # Process action
        if action == "interested":
            # Mark as interested and trigger brochure flow
            lead.notes += f"\\n[{timezone.now()}] Clicked 'Interested' via WhatsApp"
            
            # Move to interested stage if exists
            from .models import LeadStage
            interested_stage = LeadStage.objects.filter(name__icontains='interested').first()
            if interested_stage:
                lead.current_stage = interested_stage
            
            lead.save()
            
            # Trigger brochure sending
            self._send_brochure_flow(lead)
            
            return {
                "status": "success", 
                "action": "interested",
                "message": "Thank you for your interest! We'll send you the brochure.",
                "next_step": "brochure_sent"
            }
            
        elif action == "not_interested":
            # Mark as not interested and stop follow-ups
            lead.notes += f"\\n[{timezone.now()}] Clicked 'Not Interested' via WhatsApp"
            
            # Move to cold/dead stage
            from .models import LeadStage
            cold_stage = LeadStage.objects.filter(name__icontains='cold').first()
            if cold_stage:
                lead.current_stage = cold_stage
            
            lead.save()
            
            return {
                "status": "success",
                "action": "not_interested", 
                "message": "Thank you for your response. We won't send further updates.",
                "next_step": "follow_up_stopped"
            }
        
        return {"status": "error", "message": "Invalid action"}
    
    def _send_brochure_flow(self, lead: Lead):
        """Send brochure via WhatsApp when lead shows interest"""
        
        # Get project brochure
        project = lead.interested_projects.first()
        if not project or not project.brochure_pdf:
            return False
        
        brochure_url = f"{self.base_url}{project.brochure_pdf.url}"
        
        # Send brochure as document
        success, message_id, response = self.whatsapp_service.send_template_message(
            to=lead.phone,
            template_name="brochure_template",  # Separate template for brochure
            language="en",
            body_variables=[lead.name, project.name],
            header_media_url=brochure_url,
            header_media_type="document",
            lead_id=lead.id
        )
        
        return success

class WhatsAppAIPromptGenerator:
    """Generate AI prompts for WhatsApp interactive templates"""
    
    @staticmethod
    def get_system_prompt() -> str:
        """Get system prompt for AI to generate WhatsApp templates"""
        return '''You are an assistant that generates WhatsApp Business API message templates for Tata WABA integration.
Always output a valid JSON payload for the WhatsApp API.
The template must include:

Template name: project_update_template
Language: en
Body Variables:
{{1}} → Customer name
{{2}} → Project name

Footer: "Bop Realty"
Buttons:
Button 1 → "Interested ✅"
URL: https://crm.yourdomain.com/track/{{lead_id}}?token={{token}}&action=interested
Action: when clicked → mark lead as Interested + trigger brochure flow

Button 2 → "Not Interested ❌"  
URL: https://crm.yourdomain.com/track/{{lead_id}}?token={{token}}&action=not_interested
Action: when clicked → mark lead as Not Interested + stop follow-up messages

Token Format: <lead_id>:<timestamp>:<hash>
hash = HMAC_SHA256(secret, lead_id:timestamp)[:12]

Output: Valid WhatsApp interactive template JSON only, no explanation.'''
    
    @staticmethod
    def generate_template_json(customer_name: str, project_name: str, lead_id: int, token: str) -> Dict:
        """Generate template JSON for AI or direct use"""
        return {
            "name": "project_update_template",
            "language": "en", 
            "components": [
                {
                    "type": "BODY",
                    "text": f"Hi {customer_name},\\nWe shared details about *{project_name}*.\\nAre you interested in this project?"
                },
                {
                    "type": "FOOTER", 
                    "text": "Bop Realty"
                },
                {
                    "type": "BUTTONS",
                    "buttons": [
                        {
                            "type": "URL",
                            "text": "Interested ✅",
                            "url": f"https://crm.yourdomain.com/track/{lead_id}?token={token}&action=interested"
                        },
                        {
                            "type": "URL",
                            "text": "Not Interested ❌", 
                            "url": f"https://crm.yourdomain.com/track/{lead_id}?token={token}&action=not_interested"
                        }
                    ]
                }
            ]
        }