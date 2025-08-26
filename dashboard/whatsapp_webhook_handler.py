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
    """Handle WhatsApp webhooks from Tata Omni"""
    
    if request.method == "GET":
        # Webhook verification
        verify_token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        
        expected_token = getattr(settings, 'WHATSAPP_WEBHOOK_VERIFY_TOKEN', 'bop_realty_webhook_verify_2024')
        
        if verify_token == expected_token:
            logger.info("WhatsApp webhook verification successful")
            return HttpResponse(challenge)
        else:
            logger.error(f"WhatsApp webhook verification failed: {verify_token}")
            return HttpResponse("Verification failed", status=403)
    
    elif request.method == "POST":
        try:
            payload = json.loads(request.body)
            logger.info(f"WhatsApp webhook received: {json.dumps(payload, indent=2)}")
            
            # Process delivery status
            whatsapp_service = WhatsAppIntegrationService()
            success = whatsapp_service.record_delivery_status(payload)
            
            if success:
                logger.info("Delivery status recorded successfully")
                return JsonResponse({"status": "success", "message": "Status recorded"})
            else:
                logger.warning("Delivery status ignored or not processed")
                return JsonResponse({"status": "ignored", "message": "Status not processed"})
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in webhook payload: {str(e)}")
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            logger.error(f"Webhook processing error: {str(e)}")
            return JsonResponse({"error": "Processing failed"}, status=500)
    
    return JsonResponse({"error": "Method not allowed"}, status=405)

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