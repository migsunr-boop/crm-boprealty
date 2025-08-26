"""
WhatsApp Webhook Handler for Tata Omni Integration
Handles incoming delivery receipts and error codes
"""
import json
import logging
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from .whatsapp_integration import WhatsAppIntegrationService

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST", "GET"])
def whatsapp_webhook_handler(request):
    """Handle ALL webhooks - WhatsApp and IVR calls"""
    
    if request.method == "GET":
        # Webhook verification
        verify_token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        
        expected_token = getattr(settings, 'WHATSAPP_WEBHOOK_VERIFY_TOKEN', 'bop_realty_webhook_verify_2024')
        
        if verify_token == expected_token:
            logger.info("Webhook verification successful")
            return HttpResponse(challenge)
        else:
            logger.error(f"Webhook verification failed: {verify_token}")
            return HttpResponse("Verification failed", status=403)
    
    elif request.method == "POST":
        try:
            payload = json.loads(request.body)
            logger.info(f"Webhook received: {json.dumps(payload, indent=2)}")
            
            # Check if this is an IVR call
            if 'caller_id_number' in payload or 'from' in payload:
                return process_ivr_call(payload)
            
            # Otherwise process as WhatsApp delivery
            whatsapp_service = WhatsAppIntegrationService()
            success = whatsapp_service.record_delivery_status(payload)
            
            return JsonResponse({"status": "success" if success else "ignored"})
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in webhook payload: {str(e)}")
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            logger.error(f"Webhook processing error: {str(e)}")
            return JsonResponse({"error": "Processing failed"}, status=500)
    
    return JsonResponse({"error": "Method not allowed"}, status=405)

def process_ivr_call(payload):
    """Process IVR call - ACCEPT ALL CALLS"""
    from django.utils import timezone
    from .models import Lead, Project, LeadStage
    
    # Extract call data
    phone = payload.get('caller_id_number', payload.get('from', ''))
    duration = int(payload.get('duration', payload.get('billsec', 0)))
    call_to = payload.get('call_to_number', payload.get('to', ''))
    agent = payload.get('agent', 'No Agent')
    department = payload.get('department', 'General')
    
    if not phone:
        return JsonResponse({"status": "error", "message": "No phone number"})
    
    # Clean phone
    clean_phone = phone.replace('+91', '').replace(' ', '').replace('-', '')
    if len(clean_phone) == 10:
        clean_phone = '+91' + clean_phone
    
    # Check existing lead
    existing_lead = Lead.objects.filter(phone=clean_phone).first()
    if existing_lead:
        existing_lead.notes += f"\n\nNew Call: {timezone.now()}\nDuration: {duration}s\nAgent: {agent}"
        existing_lead.save()
        return JsonResponse({"status": "updated", "lead_id": existing_lead.id})
    
    # Create lead - ACCEPT ALL
    is_quality = duration > 60
    
    quality_stage, _ = LeadStage.objects.get_or_create(
        name='Quality Lead',
        defaults={'category': 'new', 'color': '#22c55e'}
    )
    
    junk_stage, _ = LeadStage.objects.get_or_create(
        name='Junk Lead',
        defaults={'category': 'dead', 'color': '#ef4444'}
    )
    
    # Map department
    dept_mapping = {
        '9911366161': 'LESISURE PARK PPC',
        '9540889595': 'TRINITY SKY PLAZOO META',
        '8860085019': 'HI LIFE',
        '7290001132': 'SMS CAMPAGIN'
    }
    
    project_name = dept_mapping.get(call_to.replace('+91', ''), department or 'General Inquiry')
    
    project, _ = Project.objects.get_or_create(
        name=project_name,
        defaults={
            'location': 'Delhi NCR',
            'description': f'Real project: {project_name}',
            'property_type': 'apartment',
            'bhk_options': '2BHK, 3BHK',
            'price_min': 5000000,
            'price_max': 15000000,
            'status': 'construction',
            'created_by_id': 1
        }
    )
    
    lead = Lead.objects.create(
        name=f"Live Caller {clean_phone[-4:]}",
        email=f"live{clean_phone[-4:]}@tata.com",
        phone=clean_phone,
        source='ivr_call',
        source_details=f"Live call - Duration: {duration}s",
        current_stage=quality_stage if is_quality else junk_stage,
        notes=f"LIVE IVR CALL\nDuration: {duration}s\nAgent: {agent}\nProject: {project_name}",
        quality_score=8 if is_quality else 2
    )
    
    lead.interested_projects.add(project)
    
    return JsonResponse({
        "status": "success",
        "lead_id": lead.id,
        "lead_type": "quality" if is_quality else "junk"
    })

@csrf_exempt
@require_http_methods(["POST"])
def whatsapp_message_webhook(request):
    """Handle incoming WhatsApp messages"""
    try:
        payload = json.loads(request.body)
        logger.info(f"WhatsApp message webhook: {json.dumps(payload, indent=2)}")
        
        # Process incoming message
        # This would handle customer replies, opt-outs, etc.
        
        return JsonResponse({"status": "received"})
        
    except Exception as e:
        logger.error(f"Message webhook error: {str(e)}")
        return JsonResponse({"error": "Processing failed"}, status=500)

@csrf_exempt  
@require_http_methods(["POST"])
def whatsapp_delivery_webhook(request):
    """Handle WhatsApp delivery receipts"""
    try:
        payload = json.loads(request.body)
        logger.info(f"WhatsApp delivery webhook: {json.dumps(payload, indent=2)}")
        
        # Process delivery receipt
        whatsapp_service = WhatsAppIntegrationService()
        success = whatsapp_service.record_delivery_status(payload)
        
        return JsonResponse({
            "status": "processed" if success else "ignored",
            "timestamp": payload.get('timestamp')
        })
        
    except Exception as e:
        logger.error(f"Delivery webhook error: {str(e)}")
        return JsonResponse({"error": "Processing failed"}, status=500)