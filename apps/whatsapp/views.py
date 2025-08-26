"""
WhatsApp Webhook Views for Tata Omni Integration
Handles incoming delivery receipts and error codes
"""
import json
import logging
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from .api import WhatsAppService
from .models import WhatsAppMessageLog

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def webhook_handler(request):
    """Handle WhatsApp webhooks from Tata Omni"""
    try:
        payload = json.loads(request.body)
        logger.info(f"WhatsApp webhook received: {payload}")
        
        # Record delivery status
        whatsapp_service = WhatsAppService()
        success = whatsapp_service.record_status(payload)
        
        if success:
            return JsonResponse({"status": "success"})
        else:
            return JsonResponse({"status": "ignored"})
            
    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook payload")
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        return JsonResponse({"error": "Processing failed"}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def webhook_verify(request):
    """Webhook verification for Tata setup"""
    verify_token = request.GET.get('hub.verify_token')
    challenge = request.GET.get('hub.challenge')
    
    if verify_token == getattr(settings, 'WHATSAPP_WEBHOOK_VERIFY_TOKEN', ''):
        return HttpResponse(challenge)
    else:
        return HttpResponse("Verification failed", status=403)