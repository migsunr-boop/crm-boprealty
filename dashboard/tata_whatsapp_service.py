"""
Production-grade Tata WhatsApp Template Messaging Service
Implements exact API specifications from Tata documentation
"""
import requests
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from .models import Lead, Project, WhatsAppMessage, IVRCallLog
import re
import time
from urllib.parse import urlparse
import mimetypes

logger = logging.getLogger(__name__)

class TataWhatsAppService:
    """Production WhatsApp service using exact Tata API specifications"""
    
    # Exact MIME types and size limits from Tata documentation
    SUPPORTED_MEDIA_TYPES = {
        'image': {
            'mime_types': ['image/jpeg', 'image/png'],
            'max_size_mb': 5,
            'extensions': ['.jpg', '.jpeg', '.png']
        },
        'video': {
            'mime_types': ['video/mp4', 'video/3gpp'],
            'max_size_mb': 16,
            'extensions': ['.mp4', '.3gp']
        },
        'document': {
            'mime_types': ['application/pdf'],
            'max_size_mb': 100,
            'extensions': ['.pdf']
        }
    }
    
    def __init__(self):
        self.base_url = settings.TATA_BASE_URL
        self.auth_token = settings.TATA_AUTH_TOKEN
        self.whatsapp_number = settings.WHATSAPP_PHONE_NUMBER
        self.headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json'
        }
        
        # Rate limiting: 100k/24h = ~1.15 msg/sec, using 0.8 msg/sec for safety
        self.rate_limit_delay = 1.25  # seconds between messages
        self.last_send_time = 0
        
    def validate_phone_number(self, phone: str) -> Tuple[bool, str]:
        """Validate E.164 phone number format"""
        # Clean phone number
        clean_phone = re.sub(r'[^\d+]', '', phone)
        
        # Ensure E.164 format
        if not clean_phone.startswith('+'):
            if clean_phone.startswith('91') and len(clean_phone) == 12:
                clean_phone = '+' + clean_phone
            elif len(clean_phone) == 10:
                clean_phone = '+91' + clean_phone
            else:
                return False, "Invalid phone number format"
        
        # Validate E.164 pattern
        e164_pattern = r'^\+[1-9]\d{6,15}$'
        if not re.match(e164_pattern, clean_phone):
            return False, "Phone number must be in E.164 format"
            
        return True, clean_phone
    
    def validate_media_url(self, media_url: str, media_type: str) -> Tuple[bool, str, Dict]:
        """Validate media URL with HEAD request to check content-type and size"""
        if not media_url:
            return True, "", {}
            
        try:
            # Parse URL
            parsed = urlparse(media_url)
            if not parsed.scheme or not parsed.netloc:
                return False, "Invalid media URL format", {}
            
            # HEAD request to validate
            response = requests.head(media_url, timeout=10, allow_redirects=True)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '').lower()
            content_length = response.headers.get('content-length')
            
            # Check MIME type
            allowed_types = self.SUPPORTED_MEDIA_TYPES.get(media_type, {}).get('mime_types', [])
            if content_type not in allowed_types:
                return False, f"Unsupported MIME type: {content_type}. Allowed: {allowed_types}", {}
            
            # Check size
            if content_length:
                size_mb = int(content_length) / (1024 * 1024)
                max_size = self.SUPPORTED_MEDIA_TYPES.get(media_type, {}).get('max_size_mb', 0)
                if size_mb > max_size:
                    return False, f"Media size {size_mb:.1f}MB exceeds limit of {max_size}MB", {}
            
            return True, "", {
                'content_type': content_type,
                'size_mb': float(content_length) / (1024 * 1024) if content_length else 0
            }
            
        except requests.RequestException as e:
            return False, f"Media URL validation failed: {str(e)}", {}
    
    def check_template_exists(self, template_name: str, language: str = 'en') -> Tuple[bool, str]:
        """Verify template exists in Tata system (placeholder - would need actual API)"""
        # This would require a template list API from Tata
        # For now, we'll assume template exists if name follows convention
        if not template_name or len(template_name) < 3:
            return False, "Template name too short"
        
        # Check for special characters (not supported in Omnichannel)
        if re.search(r'[^a-zA-Z0-9_]', template_name):
            return False, "Template name contains unsupported special characters"
            
        return True, ""
    
    def build_template_payload(self, 
                             to: str, 
                             template_name: str, 
                             language: str,
                             body_variables: List[str] = None,
                             header_media_url: str = None,
                             header_media_type: str = None,
                             custom_callback_data: str = None) -> Dict:
        """Build exact template payload per Tata API specification"""
        
        payload = {
            "to": to,
            "type": "template",
            "source": "crm_automation",
            "template": {
                "name": template_name,
                "language": {
                    "code": language
                },
                "components": []
            }
        }
        
        # Add body variables if provided
        if body_variables:
            body_component = {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": str(var)} for var in body_variables
                ]
            }
            payload["template"]["components"].append(body_component)
        
        # Add header media if provided
        if header_media_url and header_media_type:
            header_component = {
                "type": "header",
                "parameters": [
                    {
                        "type": header_media_type,
                        "link": header_media_url
                    }
                ]
            }
            payload["template"]["components"].append(header_component)
        
        # Add custom callback data for tracking
        if custom_callback_data:
            payload["metaData"] = {
                "custom_callback_data": custom_callback_data
            }
        
        return payload
    
    def rate_limit_check(self):
        """Enforce rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_send_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            logger.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
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
        """Send WhatsApp template message using exact Tata API"""
        
        try:
            # Validate phone number
            is_valid_phone, clean_phone = self.validate_phone_number(to)
            if not is_valid_phone:
                return False, clean_phone, {}
            
            # Validate template
            template_valid, template_error = self.check_template_exists(template_name, language)
            if not template_valid:
                return False, f"ERR_TEMPLATE_NOT_READY: {template_error}", {}
            
            # Validate media if provided
            if header_media_url:
                if not header_media_type:
                    return False, "ERR_MEDIA_TYPE_REQUIRED: header_media_type required when header_media_url provided", {}
                
                media_valid, media_error, media_info = self.validate_media_url(header_media_url, header_media_type)
                if not media_valid:
                    return False, f"ERR_MEDIA_UNSUPPORTED: {media_error}", {}
                
                logger.info(f"Media validated: {media_info}")
            
            # Check for button variables (not supported)
            if body_variables:
                for var in body_variables:
                    if any(keyword in str(var).lower() for keyword in ['button', 'cta', 'click']):
                        return False, "ERR_BUTTON_VARIABLES_UNSUPPORTED: Variables in buttons not supported. Use body variables for dynamic URLs", {}
            
            # Build payload
            custom_callback_data = f"lead_{lead_id}_{int(time.time())}" if lead_id else f"bulk_{int(time.time())}"
            payload = self.build_template_payload(
                to=clean_phone,
                template_name=template_name,
                language=language,
                body_variables=body_variables,
                header_media_url=header_media_url,
                header_media_type=header_media_type,
                custom_callback_data=custom_callback_data
            )
            
            # Rate limiting
            self.rate_limit_check()
            
            # Send request
            url = f"{self.base_url}/whatsapp-cloud/messages"
            logger.info(f"Sending WhatsApp message to {clean_phone} with template {template_name}")
            
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response_data = response.json()
            
            if response.status_code == 200:
                message_id = response_data.get('id', '')
                logger.info(f"WhatsApp message sent successfully. Message ID: {message_id}")
                return True, message_id, response_data
            else:
                error_msg = response_data.get('error', 'Unknown error')
                error_code = response_data.get('error_code', 'UNKNOWN')
                logger.error(f"WhatsApp send failed: {error_code} - {error_msg}")
                return False, f"{error_code}: {error_msg}", response_data
                
        except requests.RequestException as e:
            logger.error(f"WhatsApp API request failed: {str(e)}")
            return False, f"ERR_API_REQUEST_FAILED: {str(e)}", {}
        except Exception as e:
            logger.error(f"WhatsApp send error: {str(e)}")
            return False, f"ERR_INTERNAL: {str(e)}", {}
    
    def check_dnd_status(self, phone: str) -> bool:
        """Check if phone number is in DND list"""
        # This would integrate with Tata's DND API if available
        # For now, check our internal DND list
        try:
            # Check if lead has opted out
            lead = Lead.objects.filter(phone=phone).first()
            if lead and hasattr(lead, 'whatsapp_opt_out') and lead.whatsapp_opt_out:
                return True
            return False
        except:
            return False
    
    def create_whatsapp_message_record(self, 
                                     lead: Lead,
                                     template_name: str,
                                     message_content: str,
                                     phone_number: str,
                                     message_id: str = None,
                                     api_response: Dict = None) -> WhatsAppMessage:
        """Create WhatsApp message record in CRM"""
        
        return WhatsAppMessage.objects.create(
            lead=lead,
            template=None,  # Would link to template model if exists
            message_content=message_content,
            phone_number=phone_number,
            status='sent' if message_id else 'failed',
            message_id=message_id or '',
            api_response=api_response,
            sent_at=timezone.now() if message_id else None
        )

class TataWhatsAppCampaignService:
    """Campaign service for bulk WhatsApp messaging"""
    
    def __init__(self):
        self.whatsapp_service = TataWhatsAppService()
    
    def get_ivr_leads(self, 
                     project_names: List[str],
                     from_date: datetime,
                     to_date: datetime,
                     limit: int = None) -> List[Lead]:
        """Get leads filtered by project and date range (all sources)"""
        
        # Build query for ALL leads (not just IVR)
        query = Lead.objects.filter(
            created_at__gte=from_date,
            created_at__lte=to_date
        )
        
        # Filter by project names if specified
        if project_names:
            query = query.filter(
                interested_projects__name__in=project_names
            )
        
        # Exclude DND and invalid phones
        query = query.exclude(
            phone__isnull=True
        ).exclude(
            phone__exact=''
        )
        
        # Deduplicate by phone number (keep latest)
        leads = []
        seen_phones = set()
        
        for lead in query.order_by('-created_at'):
            # Validate phone format
            is_valid, clean_phone = self.whatsapp_service.validate_phone_number(lead.phone)
            if not is_valid:
                continue
                
            # Skip if phone already processed
            if clean_phone in seen_phones:
                continue
                
            # Check DND status
            if self.whatsapp_service.check_dnd_status(clean_phone):
                continue
                
            seen_phones.add(clean_phone)
            leads.append(lead)
            
            if limit and len(leads) >= limit:
                break
        
        return leads
    
    def prepare_template_variables(self, lead: Lead, project: Project = None) -> List[str]:
        """Prepare template variables from lead and project data"""
        
        variables = []
        
        # Variable 1: Lead name
        variables.append(lead.name or 'Customer')
        
        # Variable 2: Project name
        if project:
            variables.append(project.name)
        elif lead.interested_projects.exists():
            variables.append(lead.interested_projects.first().name)
        else:
            variables.append('our premium projects')
        
        # Variable 3: Deep link (per-lead tracking URL)
        deep_link = f"https://crm.boprealty.com/lead/{lead.id}?utm_source=whatsapp&utm_campaign=ivr_followup"
        variables.append(deep_link)
        
        return variables
    
    def run_campaign(self,
                    project_names: List[str],
                    from_date: datetime,
                    to_date: datetime,
                    template_name: str,
                    language: str = 'en',
                    header_media_url: str = None,
                    header_media_type: str = None,
                    dry_run: bool = False,
                    limit: int = None) -> Dict:
        """Run WhatsApp template campaign"""
        
        results = {
            'total_leads': 0,
            'valid_leads': 0,
            'sent_count': 0,
            'failed_count': 0,
            'errors': [],
            'sent_messages': [],
            'failed_messages': []
        }
        
        try:
            # Get filtered leads
            leads = self.get_ivr_leads(project_names, from_date, to_date, limit)
            results['total_leads'] = len(leads)
            
            if not leads:
                results['errors'].append("No valid leads found for the specified criteria")
                return results
            
            logger.info(f"Starting WhatsApp campaign for {len(leads)} leads")
            
            # Process each lead
            for lead in leads:
                try:
                    # Validate phone
                    is_valid, clean_phone = self.whatsapp_service.validate_phone_number(lead.phone)
                    if not is_valid:
                        results['errors'].append(f"Invalid phone for {lead.name}: {clean_phone}")
                        continue
                    
                    results['valid_leads'] += 1
                    
                    # Get associated project
                    project = lead.interested_projects.first()
                    
                    # Prepare variables
                    variables = self.prepare_template_variables(lead, project)
                    
                    # Build message content for logging
                    message_content = f"Template: {template_name}, Variables: {variables}"
                    
                    if dry_run:
                        results['sent_messages'].append({
                            'lead_id': lead.id,
                            'lead_name': lead.name,
                            'phone': clean_phone,
                            'template': template_name,
                            'variables': variables,
                            'project': project.name if project else None,
                            'status': 'dry_run'
                        })
                        results['sent_count'] += 1
                        continue
                    
                    # Send message
                    success, message_id_or_error, api_response = self.whatsapp_service.send_template_message(
                        to=clean_phone,
                        template_name=template_name,
                        language=language,
                        body_variables=variables,
                        header_media_url=header_media_url,
                        header_media_type=header_media_type,
                        lead_id=lead.id
                    )
                    
                    # Create message record
                    whatsapp_msg = self.whatsapp_service.create_whatsapp_message_record(
                        lead=lead,
                        template_name=template_name,
                        message_content=message_content,
                        phone_number=clean_phone,
                        message_id=message_id_or_error if success else None,
                        api_response=api_response
                    )
                    
                    if success:
                        results['sent_count'] += 1
                        results['sent_messages'].append({
                            'lead_id': lead.id,
                            'lead_name': lead.name,
                            'phone': clean_phone,
                            'message_id': message_id_or_error,
                            'whatsapp_record_id': whatsapp_msg.id
                        })
                        logger.info(f"Message sent to {lead.name} ({clean_phone}): {message_id_or_error}")
                    else:
                        results['failed_count'] += 1
                        results['failed_messages'].append({
                            'lead_id': lead.id,
                            'lead_name': lead.name,
                            'phone': clean_phone,
                            'error': message_id_or_error
                        })
                        logger.error(f"Failed to send to {lead.name} ({clean_phone}): {message_id_or_error}")
                
                except Exception as e:
                    results['failed_count'] += 1
                    error_msg = f"Error processing lead {lead.id}: {str(e)}"
                    results['errors'].append(error_msg)
                    logger.error(error_msg)
            
            logger.info(f"Campaign completed: {results['sent_count']} sent, {results['failed_count']} failed")
            
        except Exception as e:
            error_msg = f"Campaign failed: {str(e)}"
            results['errors'].append(error_msg)
            logger.error(error_msg)
        
        return results