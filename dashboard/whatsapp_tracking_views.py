"""
WhatsApp Interactive Tracking Views
Handle CTA button clicks and lead engagement tracking
"""
import json
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .models import Lead, IVRCallLog
from .whatsapp_interactive import WhatsAppInteractiveService, WhatsAppAIPromptGenerator

@csrf_exempt
@require_http_methods(["GET"])
def track_response(request, lead_id):
    """Handle WhatsApp CTA button clicks"""
    
    token = request.GET.get("token")
    action = request.GET.get("action")
    
    if not token or not action:
        return JsonResponse({"status": "error", "message": "Missing parameters"}, status=400)
    
    service = WhatsAppInteractiveService()
    result = service.process_lead_response(lead_id, action, token)
    
    if result["status"] == "success":
        # Return user-friendly response page
        return HttpResponse(f"""
        <html>
        <head><title>Response Recorded</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h2>Thank You!</h2>
            <p>{result["message"]}</p>
            <p><small>You can close this window.</small></p>
        </body>
        </html>
        """)
    else:
        return JsonResponse(result, status=403)

@login_required
def whatsapp_interactive(request):
    """WhatsApp Interactive dashboard"""
    
    # Get recent IVR calls for interactive messaging
    recent_calls = IVRCallLog.objects.filter(
        processed=False
    ).order_by('-start_stamp')[:50]
    
    # Get leads with recent WhatsApp interactions
    recent_interactions = Lead.objects.filter(
        whatsapp_messages__isnull=False
    ).distinct().order_by('-updated_at')[:20]
    
    context = {
        'recent_calls': recent_calls,
        'recent_interactions': recent_interactions,
        'ai_prompt': WhatsAppAIPromptGenerator.get_system_prompt()
    }
    
    return render(request, 'dashboard/whatsapp_interactive.html', context)

@login_required
@require_http_methods(["POST"])
def send_interactive_message(request):
    """Send interactive WhatsApp message to lead"""
    
    lead_id = request.POST.get('lead_id')
    project_name = request.POST.get('project_name', 'Our Project')
    
    try:
        lead = Lead.objects.get(id=lead_id)
    except Lead.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Lead not found"})
    
    service = WhatsAppInteractiveService()
    success, message_id, response = service.send_interactive_message(lead, project_name)
    
    if success:
        return JsonResponse({
            "status": "success",
            "message_id": message_id,
            "lead_name": lead.name,
            "phone": lead.phone
        })
    else:
        return JsonResponse({
            "status": "error", 
            "message": message_id,
            "response": response
        })

@login_required
def generate_ai_template(request):
    """Generate AI template for WhatsApp interactive messages"""
    
    customer_name = request.GET.get('name', 'Customer')
    project_name = request.GET.get('project', 'Our Project')
    lead_id = request.GET.get('lead_id', '12345')
    
    service = WhatsAppInteractiveService()
    token = service.generate_secure_token(int(lead_id))
    
    template = WhatsAppAIPromptGenerator.generate_template_json(
        customer_name, project_name, lead_id, token
    )
    
    return JsonResponse({
        "template": template,
        "system_prompt": WhatsAppAIPromptGenerator.get_system_prompt(),
        "token": token
    })

@login_required
def interactive_analytics(request):
    """Analytics for interactive WhatsApp campaigns"""
    
    from django.db.models import Count, Q
    from datetime import datetime, timedelta
    
    # Last 30 days analytics
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    analytics = {
        'total_sent': Lead.objects.filter(
            whatsapp_messages__created_at__gte=thirty_days_ago
        ).count(),
        
        'interested_clicks': Lead.objects.filter(
            notes__icontains='Clicked \'Interested\'',
            updated_at__gte=thirty_days_ago
        ).count(),
        
        'not_interested_clicks': Lead.objects.filter(
            notes__icontains='Clicked \'Not Interested\'',
            updated_at__gte=thirty_days_ago
        ).count(),
        
        'engagement_rate': 0,
        'conversion_rate': 0
    }
    
    # Calculate rates
    if analytics['total_sent'] > 0:
        total_clicks = analytics['interested_clicks'] + analytics['not_interested_clicks']
        analytics['engagement_rate'] = (total_clicks / analytics['total_sent']) * 100
        analytics['conversion_rate'] = (analytics['interested_clicks'] / analytics['total_sent']) * 100
    
    return JsonResponse(analytics)