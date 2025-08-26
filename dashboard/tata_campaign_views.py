"""
WhatsApp Campaign Management Views
Production-grade campaign execution and monitoring
"""
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.db import transaction
from django.contrib import messages
from datetime import datetime, timedelta
import json
import csv
import logging
from .models import Lead, Project, WhatsAppMessage
from .tata_whatsapp_service import TataWhatsAppCampaignService, TataWhatsAppService

logger = logging.getLogger(__name__)

@login_required
def whatsapp_campaign_dashboard(request):
    """WhatsApp campaign management dashboard"""
    
    # Get recent campaigns (last 30 days)
    recent_messages = WhatsAppMessage.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=30)
    ).order_by('-created_at')[:50]
    
    # Get projects for filtering
    projects = Project.objects.filter(is_active=True).order_by('name')
    
    # Campaign statistics
    stats = {
        'total_sent_today': WhatsAppMessage.objects.filter(
            created_at__date=timezone.now().date(),
            status__in=['sent', 'delivered', 'read']
        ).count(),
        'total_failed_today': WhatsAppMessage.objects.filter(
            created_at__date=timezone.now().date(),
            status='failed'
        ).count(),
        'total_sent_month': WhatsAppMessage.objects.filter(
            created_at__month=timezone.now().month,
            created_at__year=timezone.now().year,
            status__in=['sent', 'delivered', 'read']
        ).count(),
    }
    
    context = {
        'recent_messages': recent_messages,
        'projects': projects,
        'stats': stats,
        'page_title': 'WhatsApp Campaigns'
    }
    
    return render(request, 'dashboard/whatsapp_campaigns.html', context)

@login_required
@require_http_methods(["POST"])
def run_whatsapp_campaign(request):
    """Execute WhatsApp campaign with validation"""
    
    try:
        # Parse request data
        data = json.loads(request.body)
        
        # Extract parameters
        project_names = data.get('projects', [])
        from_date_str = data.get('from_date')
        to_date_str = data.get('to_date')
        template_name = data.get('template_name', '').strip()
        language = data.get('language', 'en')
        header_media_url = data.get('header_media_url', '').strip()
        header_media_type = data.get('header_media_type', '').strip()
        dry_run = data.get('dry_run', True)
        limit = data.get('limit', 100)
        
        # Validation
        if not template_name:
            return JsonResponse({'success': False, 'error': 'Template name is required'})
        
        if not from_date_str or not to_date_str:
            return JsonResponse({'success': False, 'error': 'Date range is required'})
        
        # Parse dates
        try:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d')
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d')
            
            # Add time to make it end of day
            to_date = to_date.replace(hour=23, minute=59, second=59)
            
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD'})
        
        # Validate date range
        if from_date > to_date:
            return JsonResponse({'success': False, 'error': 'From date cannot be after to date'})
        
        if (to_date - from_date).days > 90:
            return JsonResponse({'success': False, 'error': 'Date range cannot exceed 90 days'})
        
        # Validate media if provided
        if header_media_url and not header_media_type:
            return JsonResponse({'success': False, 'error': 'Media type required when media URL provided'})
        
        if header_media_type and header_media_type not in ['image', 'video', 'document']:
            return JsonResponse({'success': False, 'error': 'Invalid media type. Use: image, video, document'})
        
        # Initialize campaign service
        campaign_service = TataWhatsAppCampaignService()
        
        # Run campaign
        results = campaign_service.run_campaign(
            project_names=project_names,
            from_date=from_date,
            to_date=to_date,
            template_name=template_name,
            language=language,
            header_media_url=header_media_url or None,
            header_media_type=header_media_type or None,
            dry_run=dry_run,
            limit=limit
        )
        
        # Log campaign execution
        logger.info(f"WhatsApp campaign executed by {request.user.username}: {results}")
        
        return JsonResponse({
            'success': True,
            'results': results
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        logger.error(f"Campaign execution error: {str(e)}")
        return JsonResponse({'success': False, 'error': f'Campaign failed: {str(e)}'})

@login_required
def campaign_preview(request):
    """Generate campaign preview CSV"""
    
    try:
        # Get parameters from GET request
        project_names = request.GET.getlist('projects')
        from_date_str = request.GET.get('from_date')
        to_date_str = request.GET.get('to_date')
        limit = int(request.GET.get('limit', 100))
        
        if not from_date_str or not to_date_str:
            return JsonResponse({'success': False, 'error': 'Date range required'})
        
        # Parse dates
        from_date = datetime.strptime(from_date_str, '%Y-%m-%d')
        to_date = datetime.strptime(to_date_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        
        # Get leads
        campaign_service = TataWhatsAppCampaignService()
        leads = campaign_service.get_ivr_leads(project_names, from_date, to_date, limit)
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="whatsapp_campaign_preview_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Lead ID', 'Name', 'Phone', 'Email', 'Source', 'Created Date', 
            'Current Stage', 'Interested Projects', 'Last Contact', 'Notes'
        ])
        
        for lead in leads:
            # Mask phone numbers in preview (show last 4 digits)
            masked_phone = lead.phone[:-4] + 'XXXX' if len(lead.phone) > 4 else 'XXXX'
            
            writer.writerow([
                lead.id,
                lead.name,
                masked_phone,  # Masked for privacy in preview
                lead.email,
                lead.get_source_display(),
                lead.created_at.strftime('%Y-%m-%d %H:%M'),
                lead.current_stage.name if lead.current_stage else 'No Stage',
                ', '.join([p.name for p in lead.interested_projects.all()]),
                lead.last_contact_date.strftime('%Y-%m-%d') if lead.last_contact_date else 'Never',
                lead.notes[:100] + '...' if len(lead.notes) > 100 else lead.notes
            ])
        
        return response
        
    except Exception as e:
        logger.error(f"Preview generation error: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def template_validator(request):
    """Validate WhatsApp template"""
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            template_name = data.get('template_name', '').strip()
            language = data.get('language', 'en')
            
            if not template_name:
                return JsonResponse({'valid': False, 'error': 'Template name required'})
            
            # Initialize service
            whatsapp_service = TataWhatsAppService()
            
            # Validate template
            is_valid, error_msg = whatsapp_service.check_template_exists(template_name, language)
            
            return JsonResponse({
                'valid': is_valid,
                'error': error_msg if not is_valid else None,
                'template_name': template_name,
                'language': language
            })
            
        except Exception as e:
            return JsonResponse({'valid': False, 'error': str(e)})
    
    return JsonResponse({'valid': False, 'error': 'POST method required'})

@login_required
def media_validator(request):
    """Validate media URL for WhatsApp"""
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            media_url = data.get('media_url', '').strip()
            media_type = data.get('media_type', '').strip()
            
            if not media_url or not media_type:
                return JsonResponse({'valid': False, 'error': 'Media URL and type required'})
            
            # Initialize service
            whatsapp_service = TataWhatsAppService()
            
            # Validate media
            is_valid, error_msg, media_info = whatsapp_service.validate_media_url(media_url, media_type)
            
            return JsonResponse({
                'valid': is_valid,
                'error': error_msg if not is_valid else None,
                'media_info': media_info if is_valid else None
            })
            
        except Exception as e:
            return JsonResponse({'valid': False, 'error': str(e)})
    
    return JsonResponse({'valid': False, 'error': 'POST method required'})

@login_required
def campaign_status(request, campaign_id=None):
    """Get campaign status and delivery tracking"""
    
    try:
        # Get recent messages for status tracking
        if campaign_id:
            # If specific campaign tracking is implemented
            messages = WhatsAppMessage.objects.filter(
                id=campaign_id
            ).order_by('-created_at')
        else:
            # Get recent messages from last hour
            one_hour_ago = timezone.now() - timedelta(hours=1)
            messages = WhatsAppMessage.objects.filter(
                created_at__gte=one_hour_ago
            ).order_by('-created_at')
        
        # Build status summary
        status_summary = {}
        message_details = []
        
        for msg in messages:
            status = msg.status
            status_summary[status] = status_summary.get(status, 0) + 1
            
            message_details.append({
                'id': msg.id,
                'lead_name': msg.lead.name,
                'phone': msg.phone_number[-4:] + 'XXXX',  # Masked
                'status': status,
                'sent_at': msg.sent_at.isoformat() if msg.sent_at else None,
                'delivered_at': msg.delivered_at.isoformat() if msg.delivered_at else None,
                'message_id': msg.message_id
            })
        
        return JsonResponse({
            'success': True,
            'status_summary': status_summary,
            'message_details': message_details,
            'total_messages': len(message_details)
        })
        
    except Exception as e:
        logger.error(f"Status check error: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_http_methods(["POST"])
def webhook_delivery_status(request):
    """Webhook endpoint for WhatsApp delivery status updates"""
    
    try:
        # Parse webhook payload
        data = json.loads(request.body)
        
        # Extract status information (based on Tata webhook format)
        statuses = data.get('statuses', [])
        
        for status_data in statuses:
            message_id = status_data.get('id')
            status = status_data.get('status')  # sent, delivered, read, failed
            timestamp = status_data.get('timestamp')
            recipient_id = status_data.get('recipient_id')
            
            if not message_id or not status:
                continue
            
            # Find and update message record
            try:
                whatsapp_msg = WhatsAppMessage.objects.get(message_id=message_id)
                whatsapp_msg.status = status
                
                # Update timestamps based on status
                status_time = datetime.fromtimestamp(int(timestamp)) if timestamp else timezone.now()
                
                if status == 'delivered' and not whatsapp_msg.delivered_at:
                    whatsapp_msg.delivered_at = status_time
                elif status == 'read' and not whatsapp_msg.read_at:
                    whatsapp_msg.read_at = status_time
                elif status == 'failed' and not whatsapp_msg.failed_at:
                    whatsapp_msg.failed_at = status_time
                    # Extract failure reason if available
                    error_info = status_data.get('errors', [])
                    if error_info:
                        whatsapp_msg.failure_reason = str(error_info[0])
                
                whatsapp_msg.save()
                
                logger.info(f"Updated message {message_id} status to {status}")
                
            except WhatsAppMessage.DoesNotExist:
                logger.warning(f"WhatsApp message not found for ID: {message_id}")
                continue
        
        return JsonResponse({'success': True})
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook payload")
        return JsonResponse({'success': False, 'error': 'Invalid JSON'})
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def campaign_analytics(request):
    """Campaign analytics and reporting"""
    
    # Get date range from request
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Get campaign statistics
    messages = WhatsAppMessage.objects.filter(created_at__gte=start_date)
    
    # Status breakdown
    status_counts = {}
    for status_choice in WhatsAppMessage.STATUS_CHOICES:
        status = status_choice[0]
        count = messages.filter(status=status).count()
        status_counts[status] = count
    
    # Daily breakdown
    daily_stats = []
    for i in range(days):
        date = (timezone.now() - timedelta(days=i)).date()
        daily_messages = messages.filter(created_at__date=date)
        
        daily_stats.append({
            'date': date.isoformat(),
            'sent': daily_messages.filter(status__in=['sent', 'delivered', 'read']).count(),
            'failed': daily_messages.filter(status='failed').count(),
            'total': daily_messages.count()
        })
    
    # Top projects by message volume
    project_stats = []
    for project in Project.objects.filter(is_active=True):
        project_messages = messages.filter(lead__interested_projects=project).count()
        if project_messages > 0:
            project_stats.append({
                'project_name': project.name,
                'message_count': project_messages
            })
    
    project_stats.sort(key=lambda x: x['message_count'], reverse=True)
    
    context = {
        'status_counts': status_counts,
        'daily_stats': daily_stats[::-1],  # Reverse for chronological order
        'project_stats': project_stats[:10],  # Top 10
        'total_messages': messages.count(),
        'date_range_days': days
    }
    
    return JsonResponse(context)