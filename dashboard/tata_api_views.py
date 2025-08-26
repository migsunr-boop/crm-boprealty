from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .tata_calls_api import TATACallsAPI
import json

@login_required
def fetch_tata_calls(request):
    """AJAX endpoint to fetch TATA call records"""
    try:
        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 50))
        
        tata_api = TATACallsAPI()
        result = tata_api.get_call_records(from_date, to_date, page, limit)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def fetch_active_calls(request):
    """AJAX endpoint to fetch active calls"""
    try:
        tata_api = TATACallsAPI()
        result = tata_api.get_active_calls()
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def fetch_call_analytics(request):
    """AJAX endpoint to fetch call analytics"""
    try:
        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')
        
        tata_api = TATACallsAPI()
        result = tata_api.get_call_analytics(from_date, to_date)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def schedule_tata_call(request):
    """AJAX endpoint to schedule a call via TATA API"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            customer_name = data.get('customer_name')
            customer_number = data.get('customer_number')
            schedule_datetime = data.get('schedule_datetime')
            notes = data.get('notes', '')
            assigned_to = data.get('assigned_to', '')
            duration = int(data.get('duration', 30))
            
            tata_api = TATACallsAPI()
            result = tata_api.create_schedule_call(
                customer_name, customer_number, schedule_datetime, 
                notes, assigned_to, duration
            )
            
            return JsonResponse(result)
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def get_recording_status(request, batch_id):
    """Get recording upload status"""
    try:
        tata_api = TATACallsAPI()
        result = tata_api.get_recording_status(batch_id)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def export_call_data(request):
    """Export call data to CSV"""
    try:
        import csv
        from django.http import HttpResponse
        from datetime import datetime
        
        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')
        
        tata_api = TATACallsAPI()
        call_data = tata_api.get_call_records(from_date, to_date, limit=1000)
        
        if not call_data.get('success', True):
            return JsonResponse(call_data)
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="tata_calls_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        
        # Write header
        writer.writerow([
            'Call ID', 'Date', 'Time', 'Customer Number', 'Agent Name', 
            'Direction', 'Status', 'Duration (sec)', 'Recording URL'
        ])
        
        # Write data
        for call in call_data.get('results', []):
            writer.writerow([
                call.get('call_id', ''),
                call.get('date', ''),
                call.get('time', ''),
                call.get('client_number', ''),
                call.get('agent_name', ''),
                call.get('direction', ''),
                call.get('status', ''),
                call.get('call_duration', 0),
                call.get('recording_url', '')
            ])
        
        return response
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def tata_call_dashboard(request):
    """Real-time call dashboard"""
    try:
        tata_api = TATACallsAPI()
        
        # Get current data
        active_calls = tata_api.get_active_calls()
        analytics = tata_api.get_call_analytics()
        
        dashboard_data = {
            'active_calls': active_calls,
            'analytics': analytics,
            'timestamp': datetime.now().isoformat()
        }
        
        return JsonResponse(dashboard_data)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})