"""
WhatsApp Integration Service for Tata Tele Business Omni/Smartflo
Production-grade implementation with exact API specifications
"""
import requests
import json
import time
import re
import logging
from typing import Dict, List, Tuple
from urllib.parse import urlparse
from django.conf import settings
from django.utils import timezone
from .models import WhatsAppMessage

logger = logging.getLogger(__name__)

class WhatsAppIntegrationService:
    """Production WhatsApp service using Tata API"""
    
    SUPPORTED_MEDIA_TYPES = {
        'image': {'mime_types': ['image/jpeg', 'image/png'], 'max_size_mb': 5},
        'video': {'mime_types': ['video/mp4', 'video/3gpp'], 'max_size_mb': 16},
        'document': {'mime_types': ['application/pdf'], 'max_size_mb': 100}
    }
    
    def __init__(self):
        self.base_url = settings.TATA_BASE_URL
        self.auth_token = settings.TATA_AUTH_TOKEN
        self.headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json'
        }
        self.rate_limit_delay = getattr(settings, 'WHATSAPP_RATE_LIMIT_DELAY', 1.25)
        self.last_send_time = 0
    
    def validate_phone_number(self, phone: str) -> Tuple[bool, str]:
        """Validate and convert to E.164 format"""
        clean_phone = re.sub(r'[^\d+]', '', phone)
        
        if not clean_phone.startswith('+'):
            if clean_phone.startswith('91') and len(clean_phone) == 12:
                clean_phone = '+' + clean_phone
            elif len(clean_phone) == 10:
                clean_phone = '+91' + clean_phone
            else:
                return False, "Invalid phone number format"
        
        e164_pattern = r'^\+[1-9]\d{6,15}$'
        if not re.match(e164_pattern, clean_phone):
            return False, "Phone number must be in E.164 format"
        
        return True, clean_phone
    
    def validate_media(self, url: str, media_type: str = 'document') -> Tuple[bool, str]:
        """Validate media URL with HEAD request"""
        if not url:
            return True, ""
        
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False, "Invalid media URL format"
            
            response = requests.head(url, timeout=10, allow_redirects=True)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '').lower()
            content_length = response.headers.get('content-length')
            
            # Check MIME type
            allowed_types = self.SUPPORTED_MEDIA_TYPES.get(media_type, {}).get('mime_types', [])
            if content_type not in allowed_types:
                return False, f"Unsupported MIME type: {content_type}"
            
            # Check size
            if content_length:
                size_mb = int(content_length) / (1024 * 1024)
                max_size = self.SUPPORTED_MEDIA_TYPES.get(media_type, {}).get('max_size_mb', 0)
                if size_mb > max_size:
                    return False, f"Media size {size_mb:.1f}MB exceeds limit of {max_size}MB"
            
            return True, ""
            
        except requests.RequestException as e:
            return False, f"Media validation failed: {str(e)}"
    
    def rate_limit_check(self):
        """Enforce rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_send_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_send_time = time.time()
    
    def send_template_message(self, 
                            to: str,
                            template_name: str,
                            language: str = 'en',
                            body_variables: List[str] = None,
                            header_media_url: str = None,
                            header_media_type: str = None,
                            lead_id: int = None) -> Tuple[bool, str, Dict]:
        """Send WhatsApp template message"""
        
        try:
            # Validate phone
            is_valid, clean_phone = self.validate_phone_number(to)
            if not is_valid:
                return False, clean_phone, {}
            
            # Validate media if provided
            if header_media_url:
                media_valid, media_error = self.validate_media(header_media_url, header_media_type or 'document')
                if not media_valid:
                    return False, f"ERR_MEDIA_UNSUPPORTED: {media_error}", {}
            
            # Check for button variables (not supported)
            if body_variables:
                for var in body_variables:
                    if any(keyword in str(var).lower() for keyword in ['button', 'cta']):
                        return False, "ERR_BUTTON_VARIABLES_UNSUPPORTED", {}
            
            # Build payload
            payload = {
                "to": clean_phone,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {"code": language},
                    "components": []
                }
            }
            
            # Add body variables
            if body_variables:
                payload["template"]["components"].append({
                    "type": "body",
                    "parameters": [{"type": "text", "text": str(var)} for var in body_variables]
                })
            
            # Add header media
            if header_media_url and header_media_type:
                payload["template"]["components"].append({
                    "type": "header",
                    "parameters": [{"type": header_media_type, "link": header_media_url}]
                })
            
            # Rate limiting
            self.rate_limit_check()
            
            # Try direct API first
            success, message_id, response_data = self._send_direct_api(payload)
            
            if not success:
                # Fallback to Omni Automation Webhook
                success, message_id, response_data = self._send_via_omni_webhook(payload)
            
            # Create message record
            if lead_id:
                from .models import Lead
                lead = Lead.objects.filter(id=lead_id).first()
                if lead:
                    WhatsAppMessage.objects.create(
                        lead=lead,
                        message_content=f"Template: {template_name}, Variables: {body_variables}",
                        phone_number=clean_phone,
                        status='sent' if success else 'failed',
                        message_id=message_id if success else '',
                        api_response=response_data,
                        sent_at=timezone.now() if success else None,
                        failure_reason=message_id if not success else ''
                    )
            
            return success, message_id, response_data
                
        except Exception as e:
            logger.error(f"WhatsApp send error: {str(e)}")
            return False, f"ERR_INTERNAL: {str(e)}", {}
    
    def _send_direct_api(self, payload: Dict) -> Tuple[bool, str, Dict]:
        """Send via direct WhatsApp Cloud API"""
        try:
            url = f"{self.base_url}/whatsapp-cloud/messages"
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                message_id = response_data.get('id', '')
                logger.info(f"WhatsApp message sent via direct API: {message_id}")
                return True, message_id, response_data
            else:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('error', 'Direct API failed')
                return False, error_msg, error_data
                
        except Exception as e:
            logger.error(f"Direct API error: {str(e)}")
            return False, f"Direct API failed: {str(e)}", {}
    
    def _send_via_omni_webhook(self, payload: Dict) -> Tuple[bool, str, Dict]:
        """Fallback: Send via Omni Automation Webhook"""
        try:
            # Transform payload for Omni webhook
            omni_payload = {
                "integration_id": getattr(settings, 'CRM_API_INTEGRATION_ID', ''),
                "action": "send_whatsapp_template",
                "data": payload
            }
            
            webhook_url = f"{self.base_url}/automation/webhook"
            response = requests.post(webhook_url, headers=self.headers, json=omni_payload, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                logger.info("WhatsApp message sent via Omni webhook")
                return True, "sent_via_webhook", response_data
            else:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('error', 'Webhook send failed')
                return False, error_msg, error_data
                
        except Exception as e:
            logger.error(f"Omni webhook error: {str(e)}")
            return False, f"Webhook failed: {str(e)}", {}
    
    def record_delivery_status(self, webhook_payload: Dict):
        """Record delivery status from webhook"""
        try:
            message_id = webhook_payload.get('id')
            status = webhook_payload.get('status', {}).get('status')
            
            if message_id and status:
                message = WhatsAppMessage.objects.filter(message_id=message_id).first()
                if message:
                    message.status = status.lower()
                    
                    if status.lower() == 'delivered':
                        message.delivered_at = timezone.now()
                    elif status.lower() == 'read':
                        message.read_at = timezone.now()
                    
                    message.api_response = webhook_payload
                    message.save()
                    
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Status recording error: {str(e)}")
            return False