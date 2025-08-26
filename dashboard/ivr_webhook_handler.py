"""
IVR Webhook Handler - Accept ALL calls from TATA
"""
import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import datetime
from .models import Lead, Project, LeadStage

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def ivr_webhook_handler(request):
    """Accept ALL IVR calls from TATA - no filtering"""
    
    try:
        payload = json.loads(request.body)
        logger.info(f"IVR webhook received: {json.dumps(payload, indent=2)}")
        
        # Extract call data
        phone = payload.get('caller_id_number', payload.get('from', ''))
        duration = int(payload.get('duration', payload.get('billsec', 0)))
        call_to = payload.get('call_to_number', payload.get('to', ''))
        status = payload.get('status', 'received')
        agent = payload.get('agent', 'No Agent')
        department = payload.get('department', 'General')
        call_time = payload.get('start_time', timezone.now().isoformat())
        call_id = payload.get('call_id', f"ivr_{phone}_{int(timezone.now().timestamp())}")
        
        if not phone:
            return JsonResponse({"status": "error", "message": "No phone number"}, status=400)
        
        # Clean phone number
        clean_phone = phone.replace('+91', '').replace(' ', '').replace('-', '')
        if len(clean_phone) == 10:
            clean_phone = '+91' + clean_phone
        elif not clean_phone.startswith('+91'):
            clean_phone = '+91' + clean_phone[-10:]
        
        # Check if lead already exists
        existing_lead = Lead.objects.filter(phone=clean_phone).first()
        
        if existing_lead:
            # Update existing lead with new call info
            existing_lead.notes += f"\n\nNew Call: {call_time}\nDuration: {duration}s\nAgent: {agent}\nStatus: {status}"
            existing_lead.save()
            
            return JsonResponse({
                "status": "updated",
                "message": f"Updated existing lead {existing_lead.id}",
                "lead_id": existing_lead.id
            })
        
        # Create new lead - ACCEPT ALL CALLS
        # Determine quality AFTER creation, not before
        is_quality = duration > 60
        
        # Get or create stages
        quality_stage, _ = LeadStage.objects.get_or_create(
            name='Quality Lead',
            defaults={'category': 'new', 'color': '#22c55e', 'order': 1}
        )
        
        junk_stage, _ = LeadStage.objects.get_or_create(
            name='Junk Lead',
            defaults={'category': 'dead', 'color': '#ef4444', 'order': 99}
        )
        
        stage = quality_stage if is_quality else junk_stage
        
        # Map department to project
        department_mapping = {
            '9911366161': 'LESISURE PARK PPC',
            '9540889595': 'TRINITY SKY PLAZOO META',
            '8860085019': 'HI LIFE',
            '7290001132': 'SMS CAMPAGIN',
            '9654444333': 'General Inquiry'
        }
        
        project_name = department_mapping.get(call_to.replace('+91', ''), department or 'General Inquiry')
        
        # Create project if not exists
        project, _ = Project.objects.get_or_create(
            name=project_name,
            defaults={
                'location': 'Delhi NCR',
                'description': f'Real project from IVR: {project_name}',
                'property_type': 'apartment',
                'bhk_options': '2BHK, 3BHK',
                'price_min': 5000000,
                'price_max': 15000000,
                'status': 'construction',
                'created_by_id': 1
            }
        )
        
        # Create lead - ALWAYS CREATE, NEVER FILTER
        lead = Lead.objects.create(
            name=f"IVR Lead {clean_phone[-4:]}",
            email=f"ivr{clean_phone[-4:]}@tata.com",
            phone=clean_phone,
            source='ivr_call',
            source_details=f"IVR Call ID: {call_id} - Duration: {duration}s",
            current_stage=stage,
            notes=f"IVR CALL\\nTime: {call_time}\\nDuration: {duration}s\\nAgent: {agent}\\nDepartment: {project_name}\\nStatus: {status}\\nCall ID: {call_id}",
            quality_score=8 if is_quality else 2
        )
        
        # Associate with project
        lead.interested_projects.add(project)
        
        logger.info(f"Created lead {lead.id} from IVR call {call_id}")
        
        return JsonResponse({
            "status": "success",
            "message": f"Lead created successfully",
            "lead_id": lead.id,
            "lead_type": "quality" if is_quality else "junk"
        })
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in IVR webhook: {str(e)}")
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"IVR webhook error: {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)