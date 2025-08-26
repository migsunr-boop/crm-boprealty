"""
IVR Leads Dashboard Views
Display and manage leads created from IVR calls
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Lead, IVRCallLog, Project
from .ivr_lead_creator import IVRLeadCreator

@login_required
def ivr_leads_dashboard(request):
    """IVR Leads dashboard with statistics and management"""
    
    creator = IVRLeadCreator()
    stats = creator.get_lead_statistics()
    
    # Get recent IVR calls (processed and unprocessed)
    recent_calls = IVRCallLog.objects.all().order_by('-start_stamp')[:20]
    
    # Get IVR leads by quality
    quality_leads = Lead.objects.filter(
        source='ivr_call'
    ).exclude(current_stage__name='Junk Lead').order_by('-created_at')[:10]
    
    junk_leads = Lead.objects.filter(
        source='ivr_call',
        current_stage__name='Junk Lead'
    ).order_by('-created_at')[:10]
    
    context = {
        'stats': stats,
        'recent_calls': recent_calls,
        'quality_leads': quality_leads,
        'junk_leads': junk_leads,
        'unprocessed_count': IVRCallLog.objects.filter(processed=False).count()
    }
    
    return render(request, 'dashboard/ivr_leads.html', context)

@login_required
@require_http_methods(["POST"])
def process_ivr_calls(request):
    """Process unprocessed IVR calls into leads"""
    
    creator = IVRLeadCreator()
    results = creator.process_unprocessed_calls()
    
    return JsonResponse({
        'status': 'success',
        'results': results
    })

@login_required
def ivr_lead_analytics(request):
    """Get IVR lead analytics data"""
    
    creator = IVRLeadCreator()
    stats = creator.get_lead_statistics()
    
    # Additional analytics
    from django.db.models import Count, Avg
    
    # Call duration analysis
    call_analysis = IVRCallLog.objects.filter(
        associated_lead__isnull=False
    ).aggregate(
        avg_duration=Avg('duration'),
        total_calls=Count('id')
    )
    
    # Lead conversion by project
    project_conversion = []
    for project_name, counts in stats['by_project'].items():
        if counts['total'] > 0:
            conversion_rate = (counts['quality'] / counts['total']) * 100
            project_conversion.append({
                'project': project_name,
                'total': counts['total'],
                'quality': counts['quality'],
                'junk': counts['junk'],
                'conversion_rate': round(conversion_rate, 1)
            })
    
    return JsonResponse({
        'stats': stats,
        'call_analysis': call_analysis,
        'project_conversion': project_conversion
    })