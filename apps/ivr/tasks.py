"""
IVR Lead Processing Tasks
Query last 1000 calls, group by project/status, enqueue WhatsApp sends
"""
import re
from datetime import datetime, timedelta
from django.db.models import Q
from django.utils import timezone
from .models import IVRCall
from dashboard.models import Lead, Project
from apps.whatsapp.api import WhatsAppService

class IVRLeadProcessor:
    def __init__(self):
        self.whatsapp_service = WhatsAppService()
    
    def get_last_1000_calls(self):
        """Fetch last 1000 IVR calls ordered by created_at desc"""
        return IVRCall.objects.all().order_by('-created_at')[:1000]
    
    def validate_e164_phone(self, phone):
        """Validate and convert to E.164 format"""
        clean_phone = re.sub(r'[^\d+]', '', phone)
        
        if not clean_phone.startswith('+'):
            if clean_phone.startswith('91') and len(clean_phone) == 12:
                clean_phone = '+' + clean_phone
            elif len(clean_phone) == 10:
                clean_phone = '+91' + clean_phone
            else:
                return None
        
        e164_pattern = r'^\+[1-9]\d{6,15}$'
        if re.match(e164_pattern, clean_phone):
            return clean_phone
        return None
    
    def check_dnd_list(self, phone):
        """Check if phone is in CRM DND list"""
        # Check if lead has opted out
        lead = Lead.objects.filter(phone=phone).first()
        return lead and hasattr(lead, 'whatsapp_opt_out') and lead.whatsapp_opt_out
    
    def deduplicate_by_phone(self, calls):
        """Deduplicate calls by phone number, keep latest"""
        seen_phones = set()
        unique_calls = []
        
        for call in calls:
            clean_phone = self.validate_e164_phone(call.phone_number)
            if not clean_phone:
                continue
                
            if clean_phone in seen_phones:
                continue
                
            if self.check_dnd_list(clean_phone):
                continue
                
            seen_phones.add(clean_phone)
            unique_calls.append(call)
        
        return unique_calls
    
    def group_calls_by_project_status(self, calls):
        """Group calls by project_name then by status"""
        grouped = {}
        
        for call in calls:
            project = call.project_name
            status = call.status
            
            if project not in grouped:
                grouped[project] = {}
            
            if status not in grouped[project]:
                grouped[project][status] = []
            
            grouped[project][status].append(call)
        
        return grouped
    
    def process_ivr_leads(self, dry_run=False):
        """Main processing function"""
        # Fetch last 1000 calls
        calls = self.get_last_1000_calls()
        
        # Deduplicate by phone number
        unique_calls = self.deduplicate_by_phone(calls)
        
        # Group by project and status
        grouped_calls = self.group_calls_by_project_status(unique_calls)
        
        results = {
            'total_calls': len(calls),
            'unique_calls': len(unique_calls),
            'grouped_data': grouped_calls,
            'whatsapp_queue': []
        }
        
        # Enqueue WhatsApp messages
        for project_name, statuses in grouped_calls.items():
            for status, call_list in statuses.items():
                for call in call_list:
                    clean_phone = self.validate_e164_phone(call.phone_number)
                    if clean_phone:
                        whatsapp_payload = self.create_whatsapp_payload(call, clean_phone)
                        results['whatsapp_queue'].append(whatsapp_payload)
                        
                        if not dry_run:
                            # Send WhatsApp message
                            self.whatsapp_service.send_template_message(
                                to=clean_phone,
                                template_name=whatsapp_payload['template']['name'],
                                language=whatsapp_payload['template']['language'],
                                body_variables=whatsapp_payload.get('body_variables', []),
                                header_media_url=whatsapp_payload.get('header_media_url'),
                                header_media_type=whatsapp_payload.get('header_media_type')
                            )
        
        return results
    
    def create_whatsapp_payload(self, call, clean_phone):
        """Create WhatsApp template payload for IVR call"""
        # Map call status to template
        template_name = "project_update_template"  # Default template
        
        # Get lead name if exists
        lead = Lead.objects.filter(phone__icontains=clean_phone[-10:]).first()
        lead_name = lead.name if lead else "Customer"
        
        # Get project brochure URL if exists
        project = Project.objects.filter(name__icontains=call.project_name).first()
        brochure_url = None
        if project and project.brochure_pdf:
            brochure_url = f"https://crm-1z7t.onrender.com{project.brochure_pdf.url}"
        
        payload = {
            "to": clean_phone,
            "template": {
                "name": template_name,
                "language": "en",
                "components": []
            }
        }
        
        # Body variables
        body_variables = [lead_name, call.project_name, call.status.title()]
        payload["body_variables"] = body_variables
        
        # Header media if available
        if brochure_url:
            payload["header_media_url"] = brochure_url
            payload["header_media_type"] = "document"
        
        return payload