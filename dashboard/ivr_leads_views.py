"""
IVR Leads Dashboard Views
Display and manage leads created from IVR calls
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import datetime
from .models import Lead, IVRCallLog, Project

@login_required
def ivr_leads_dashboard(request):
    """IVR Leads dashboard with statistics and management"""
    
    # Get IVR lead statistics
    total_ivr_leads = Lead.objects.filter(source='ivr_call').count()
    quality_leads_count = Lead.objects.filter(source='ivr_call').exclude(current_stage__name='Junk Lead').count()
    junk_leads_count = Lead.objects.filter(source='ivr_call', current_stage__name='Junk Lead').count()
    
    stats = {
        'total_leads': total_ivr_leads,
        'quality_leads': quality_leads_count,
        'junk_leads': junk_leads_count,
        'conversion_rate': round((quality_leads_count / total_ivr_leads * 100) if total_ivr_leads > 0 else 0, 1)
    }
    
    # Get recent data
    recent_calls = IVRCallLog.objects.all().order_by('-start_stamp')[:20]
    quality_leads = Lead.objects.filter(source='ivr_call').exclude(current_stage__name='Junk Lead').order_by('-created_at')[:10]
    junk_leads = Lead.objects.filter(source='ivr_call', current_stage__name='Junk Lead').order_by('-created_at')[:10]
    
    context = {
        'stats': stats,
        'recent_calls': recent_calls,
        'quality_leads': quality_leads,
        'junk_leads': junk_leads,
        'unprocessed_count': 0
    }
    
    return render(request, 'dashboard/ivr_leads.html', context)

@login_required
@require_http_methods(["POST"])
def send_whatsapp_to_ivr_leads(request):
    """Send WhatsApp templates to today's IVR leads"""
    from .ivr_whatsapp_campaign import IVRWhatsAppCampaign
    
    campaign = IVRWhatsAppCampaign()
    results = campaign.send_to_todays_leads()
    
    return JsonResponse({
        'status': 'success',
        'results': results,
        'message': f"Sent to {results['sent_successfully']} leads, {results['failed']} failed"
    })

@login_required
def ivr_lead_analytics(request):
    """Get IVR lead analytics data"""
    from django.db.models import Count, Avg
    
    # Basic stats
    total_leads = Lead.objects.filter(source='ivr_call').count()
    quality_leads = Lead.objects.filter(source='ivr_call').exclude(current_stage__name='Junk Lead').count()
    junk_leads = Lead.objects.filter(source='ivr_call', current_stage__name='Junk Lead').count()
    
    stats = {
        'total_leads': total_leads,
        'quality_leads': quality_leads, 
        'junk_leads': junk_leads
    }
    
    # Call analysis
    call_analysis = IVRCallLog.objects.aggregate(
        avg_duration=Avg('duration'),
        total_calls=Count('id')
    )
    
    return JsonResponse({
        'stats': stats,
        'call_analysis': call_analysis
    })

@login_required
@require_http_methods(["POST"])
def sync_ivr_data(request):
    """Sync latest TATA calls to leads"""
    from .tata_live_sync import TATALiveSync
    
    try:
        # Sync latest calls from TATA
        sync = TATALiveSync()
        results = sync.sync_to_leads()
        
        return JsonResponse({
            'status': 'success',
            'summary': {
                'total_calls': results['total_calls'],
                'new_leads_created': results['new_leads'],
                'updated_leads': results['updated_leads']
            },
            'message': f"Synced {results['total_calls']} latest calls. Created {results['new_leads']} new leads."
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

