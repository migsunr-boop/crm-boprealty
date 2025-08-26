"""
Tata WhatsApp Webhook Handler
Handles delivery status updates and message events
"""
import json
import logging
import hashlib
import hmac
from datetime import datetime
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.conf import settings
from django.utils import timezone
from .models import WhatsAppMessage, Lead, LeadNote
import requests

logger = logging.getLogger(__name__)

class TataWebhookHandler:
    """Handle Tata WhatsApp webhooks for delivery status and messages"""
    
    def __init__(self):
        self.verify_token = getattr(settings, 'WHATSAPP_WEBHOOK_VERIFY_TOKEN', '')
    
    def verify_webhook_signature(self, payload, signature):
        """Verify webhook signature using partner token"""
        if not self.verify_token:
            logger.warning("Webhook verify token not configured")
            return True  # Skip verification if not configured
        
        try:
            # Generate signature
            expected_signature = hmac.new(
                self.verify_token.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(f"sha256={expected_signature}", signature)
            
        except Exception as e:
            logger.error(f"Signature verification failed: {str(e)}")
            return False
    
    def handle_delivery_status(self, webhook_data):
        """Handle message delivery status updates"""
        try:
            statuses = webhook_data.get('statuses', [])
            updated_count = 0
            
            for status_data in statuses:
                message_id = status_data.get('id')
                status = status_data.get('status')  # sent, delivered, read, failed
                timestamp = status_data.get('timestamp')
                recipient_id = status_data.get('recipient_id')
                custom_callback_data = status_data.get('custom_callback_data')
                
                if not message_id or not status:
                    logger.warning(f"Invalid status data: {status_data}")
                    continue
                
                # Find message record
                try:
                    whatsapp_msg = WhatsAppMessage.objects.get(message_id=message_id)
                    
                    # Update status
                    old_status = whatsapp_msg.status
                    whatsapp_msg.status = status
                    
                    # Update timestamps
                    if timestamp:
                        status_time = datetime.fromtimestamp(int(timestamp))
                        status_time = timezone.make_aware(status_time)
                    else:
                        status_time = timezone.now()
                    
                    if status == 'delivered' and not whatsapp_msg.delivered_at:
                        whatsapp_msg.delivered_at = status_time
                    elif status == 'read' and not whatsapp_msg.read_at:
                        whatsapp_msg.read_at = status_time
                    elif status == 'failed' and not whatsapp_msg.failed_at:
                        whatsapp_msg.failed_at = status_time
                        
                        # Extract failure reason
                        errors = status_data.get('errors', [])
                        if errors:
                            error_info = errors[0]
                            whatsapp_msg.failure_reason = f"{error_info.get('code', 'UNKNOWN')}: {error_info.get('title', 'Unknown error')}"
                    
                    whatsapp_msg.save()
                    updated_count += 1
                    
                    logger.info(f"Updated message {message_id}: {old_status} -> {status}")
                    
                    # Create lead note for status change
                    if whatsapp_msg.lead and status in ['delivered', 'read', 'failed']:
                        self.create_status_note(whatsapp_msg, status, status_time)
                
                except WhatsAppMessage.DoesNotExist:
                    logger.warning(f"WhatsApp message not found for ID: {message_id}")
                    continue
                except Exception as e:
                    logger.error(f"Error updating message {message_id}: {str(e)}")
                    continue
            
            return {'updated_count': updated_count}
            
        except Exception as e:
            logger.error(f"Error handling delivery status: {str(e)}")
            raise
    
    def handle_incoming_message(self, webhook_data):
        """Handle incoming WhatsApp messages from users"""
        try:
            contacts = webhook_data.get('contacts', [])
            messages = webhook_data.get('messages', {})
            business_phone = webhook_data.get('businessPhoneNumber', '')
            
            # Extract message data
            from_number = messages.get('from', '')
            message_id = messages.get('id', '')
            timestamp = messages.get('timestamp', '')
            message_type = messages.get('type', '')
            
            # Get message content based on type
            message_content = ''
            if message_type == 'text':
                message_content = messages.get('text', {}).get('body', '')
            elif message_type == 'image':
                message_content = '[Image received]'
            elif message_type == 'video':
                message_content = '[Video received]'
            elif message_type == 'document':
                message_content = '[Document received]'
            elif message_type == 'audio':
                message_content = '[Audio received]'
            else:
                message_content = f'[{message_type} message]'
            
            # Get contact info
            contact_name = ''
            if contacts:
                contact_name = contacts[0].get('profile', {}).get('name', '')
            
            # Find associated lead
            lead = self.find_lead_by_phone(from_number)
            
            if lead:
                # Create lead note for incoming message
                LeadNote.objects.create(
                    lead=lead,
                    call_type='whatsapp',
                    call_outcome='message_received',
                    note=f"Incoming WhatsApp message: {message_content}",
                    created_by_id=1  # System user
                )
                
                logger.info(f"Incoming WhatsApp from {lead.name} ({from_number}): {message_content}")
            else:
                logger.info(f"Incoming WhatsApp from unknown number {from_number}: {message_content}")
            
            return {
                'message_id': message_id,
                'from_number': from_number,
                'lead_found': lead is not None,
                'lead_id': lead.id if lead else None
            }
            
        except Exception as e:
            logger.error(f"Error handling incoming message: {str(e)}")
            raise
    
    def create_status_note(self, whatsapp_msg, status, timestamp):
        """Create lead note for WhatsApp status updates"""
        try:
            status_messages = {
                'delivered': 'WhatsApp message delivered',
                'read': 'WhatsApp message read by customer',
                'failed': f'WhatsApp message failed: {whatsapp_msg.failure_reason}'
            }
            
            note_content = status_messages.get(status, f'WhatsApp status: {status}')
            
            LeadNote.objects.create(
                lead=whatsapp_msg.lead,
                call_type='whatsapp',
                call_outcome=status,
                note=note_content,
                created_by_id=1  # System user
            )
            
        except Exception as e:
            logger.error(f"Error creating status note: {str(e)}")
    
    def find_lead_by_phone(self, phone_number):
        """Find lead by phone number with fuzzy matching"""
        try:
            # Clean phone number
            clean_phone = phone_number.replace('+91', '').replace(' ', '').replace('-', '')
            
            # Try exact match first
            lead = Lead.objects.filter(phone=phone_number).first()
            if lead:
                return lead
            
            # Try with +91 prefix
            lead = Lead.objects.filter(phone=f'+91{clean_phone}').first()
            if lead:
                return lead
            
            # Try fuzzy match on last 10 digits
            if len(clean_phone) >= 10:
                last_10 = clean_phone[-10:]
                lead = Lead.objects.filter(phone__icontains=last_10).first()
                if lead:
                    return lead
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding lead by phone {phone_number}: {str(e)}")
            return None

# Webhook view functions
webhook_handler = TataWebhookHandler()

@csrf_exempt
@require_http_methods(["POST", "GET"])
def whatsapp_webhook(request):
    """Main WhatsApp webhook endpoint"""
    
    if request.method == 'GET':
        # Webhook verification (if Tata requires it)
        verify_token = request.GET.get('hub.verify_token', '')
        challenge = request.GET.get('hub.challenge', '')
        
        if verify_token == webhook_handler.verify_token:
            return HttpResponse(challenge)
        else:
            return HttpResponse('Verification failed', status=403)
    
    elif request.method == 'POST':
        try:
            # Get signature for verification
            signature = request.headers.get('x-hub-signature-256', '')
            
            # Verify signature if configured
            if webhook_handler.verify_token and signature:
                if not webhook_handler.verify_webhook_signature(request.body, signature):
                    logger.warning("Webhook signature verification failed")
                    return JsonResponse({'error': 'Invalid signature'}, status=403)
            
            # Parse webhook data
            webhook_data = json.loads(request.body)
            
            # Determine webhook type and handle accordingly
            if 'statuses' in webhook_data:
                # Delivery status update
                result = webhook_handler.handle_delivery_status(webhook_data)
                logger.info(f"Processed delivery status webhook: {result}")
                
            elif 'messages' in webhook_data:
                # Incoming message
                result = webhook_handler.handle_incoming_message(webhook_data)
                logger.info(f"Processed incoming message webhook: {result}")
                
            else:
                logger.warning(f"Unknown webhook type: {webhook_data}")
                return JsonResponse({'error': 'Unknown webhook type'}, status=400)
            
            return JsonResponse({'success': True, 'result': result})
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON in webhook payload")
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Webhook processing error: {str(e)}")
            return JsonResponse({'error': 'Processing failed'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def whatsapp_delivery_webhook(request):
    """Dedicated endpoint for delivery status updates"""
    
    try:
        # Verify signature
        signature = request.headers.get('x-hub-signature-256', '')
        if webhook_handler.verify_token and signature:
            if not webhook_handler.verify_webhook_signature(request.body, signature):
                return JsonResponse({'error': 'Invalid signature'}, status=403)
        
        # Parse and handle delivery status
        webhook_data = json.loads(request.body)
        result = webhook_handler.handle_delivery_status(webhook_data)
        
        return JsonResponse({'success': True, 'updated': result['updated_count']})
        
    except Exception as e:
        logger.error(f"Delivery webhook error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def whatsapp_message_webhook(request):
    """Dedicated endpoint for incoming messages"""
    
    try:
        # Verify signature
        signature = request.headers.get('x-hub-signature-256', '')
        if webhook_handler.verify_token and signature:
            if not webhook_handler.verify_webhook_signature(request.body, signature):
                return JsonResponse({'error': 'Invalid signature'}, status=403)
        
        # Parse and handle incoming message
        webhook_data = json.loads(request.body)
        result = webhook_handler.handle_incoming_message(webhook_data)
        
        return JsonResponse({'success': True, 'result': result})
        
    except Exception as e:
        logger.error(f"Message webhook error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)