"""
WhatsApp API Service for Tata Tele Business Omni/Smartflo
Implements exact API specifications with error handling
"""
import requests
import json
import time
import re
from typing import Dict, List, Tuple, Optional
from urllib.parse import urlparse
from django.conf import settings
from django.utils import timezone
from .models import WhatsAppMessageLog
import logging

logger = logging.getLogger(__name__)

class WhatsAppService:
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
                            header_media_type: str = None) -> Tuple[bool, str, Dict]:
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
            url = f"{self.base_url}/whatsapp-cloud/messages"
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                message_id = response_data.get('id', '')
                
                # Log success
                WhatsAppMessageLog.objects.create(
                    phone=clean_phone,
                    template_name=template_name,
                    status='sent',
                    message_id=message_id,
                    webhook_payload=response_data
                )
                
                return True, message_id, response_data
            else:
                # Fallback to Omni Automation Webhook
                return self._send_via_omni_webhook(payload, clean_phone, template_name)
                
        except Exception as e:
            logger.error(f"WhatsApp send error: {str(e)}")
            return False, f"ERR_INTERNAL: {str(e)}", {}
    
    def _send_via_omni_webhook(self, payload: Dict, phone: str, template_name: str) -> Tuple[bool, str, Dict]:
        """Fallback: Send via Omni Automation Webhook"""
        try:
            # Transform payload for Omni webhook
            omni_payload = {
                "integration_id": settings.CRM_API_INTEGRATION_ID,
                "action": "send_whatsapp_template",
                "data": payload
            }
            
            webhook_url = f"{self.base_url}/automation/webhook"
            response = requests.post(webhook_url, headers=self.headers, json=omni_payload, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Log success
                WhatsAppMessageLog.objects.create(
                    phone=phone,
                    template_name=template_name,
                    status='sent',
                    webhook_payload=response_data
                )
                
                return True, "sent_via_webhook", response_data
            else:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('error', 'Webhook send failed')
                
                # Log failure
                WhatsAppMessageLog.objects.create(
                    phone=phone,
                    template_name=template_name,
                    status='failed',
                    error_code=str(response.status_code),
                    webhook_payload=error_data
                )
                
                return False, error_msg, error_data
                
        except Exception as e:
            logger.error(f"Omni webhook error: {str(e)}")
            return False, f"ERR_WEBHOOK_FAILED: {str(e)}", {}
    
    def record_status(self, webhook_payload: Dict):
        """Record delivery status from webhook"""
        try:
            message_id = webhook_payload.get('id')
            status = webhook_payload.get('status', {}).get('status')
            
            if message_id and status:
                log_entry = WhatsAppMessageLog.objects.filter(message_id=message_id).first()
                if log_entry:
                    log_entry.status = status.lower()
                    
                    if status.lower() == 'delivered':
                        log_entry.delivered_at = timezone.now()
                    elif status.lower() == 'read':
                        log_entry.read_at = timezone.now()
                    
                    log_entry.webhook_payload = webhook_payload
                    log_entry.save()
                    
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Status recording error: {str(e)}")
            return False