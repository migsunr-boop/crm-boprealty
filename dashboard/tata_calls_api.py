import requests
import json
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone

class TATACallsAPI:
    """TATA API integration for call details, recordings, and reports"""
    
    def __init__(self):
        self.base_url = "https://api-smartflo.tatateleservices.com/v1"
        self.whatsapp_url = "https://wb.omni.tatatelebusiness.com"
        self.auth_token = getattr(settings, 'TATA_AUTH_TOKEN', '')
        self.whatsapp_token = getattr(settings, 'TATA_WHATSAPP_TOKEN', '')
        self.phone_number = getattr(settings, 'TATA_PHONE_NUMBER', '+919355421616')
        self.phone_number_id = getattr(settings, 'TATA_PHONE_NUMBER_ID', '100551679754887')
    
    def get_headers(self):
        """Get authorization headers"""
        return {
            'Authorization': f'Bearer {self.auth_token}',
            'Accept': 'application/json'
        }
    
    def get_whatsapp_headers(self):
        """Get WhatsApp API headers"""
        return {
            'Authorization': f'Bearer {self.whatsapp_token}',
            'Content-Type': 'application/json'
        }
    
    def get_call_records(self, from_date=None, to_date=None, page=1, limit=50):
        """Fetch call detail records"""
        try:
            if not from_date:
                from_date = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
            if not to_date:
                to_date = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            
            url = f"{self.base_url}/call/records"
            params = {
                'from_date': from_date,
                'to_date': to_date,
                'page': page,
                'limit': limit
            }
            
            response = requests.get(url, params=params, headers=self.get_headers())
            
            if response.status_code == 200:
                return response.json()
            return {'success': False, 'error': f'API Error: {response.status_code}'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_active_calls(self):
        """Fetch active/live calls"""
        try:
            url = f"{self.base_url}/live_calls"
            response = requests.get(url, headers=self.get_headers())
            
            if response.status_code == 200:
                return {'success': True, 'data': response.json()}
            return {'success': False, 'error': f'API Error: {response.status_code}'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_recording_status(self, batch_id):
        """Get recording upload status"""
        try:
            url = f"{self.base_url}/recording/batch_status/{batch_id}"
            response = requests.get(url, headers=self.get_headers())
            
            if response.status_code == 200:
                return response.json()
            return {'success': False, 'error': f'API Error: {response.status_code}'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_schedule_call(self, customer_name, customer_number, schedule_datetime, notes="", assigned_to="", duration=30):
        """Create a scheduled call"""
        try:
            url = f"{self.base_url}/schedule_call"
            payload = {
                'customer_name': customer_name,
                'customer_number': customer_number,
                'schedule_callback_date_time': schedule_datetime,
                'schedule_callback_text': notes,
                'assigned_to': assigned_to,
                'call_end_min': str(duration)
            }
            
            response = requests.post(url, json=payload, headers=self.get_headers())
            
            if response.status_code == 200:
                return response.json()
            return {'success': False, 'error': f'API Error: {response.status_code}'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_time_groups(self):
        """Fetch all time groups"""
        try:
            url = f"{self.base_url}/timegroups"
            response = requests.get(url, headers=self.get_headers())
            
            if response.status_code == 200:
                return {'success': True, 'data': response.json()}
            return {'success': False, 'error': f'API Error: {response.status_code}'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_call_analytics(self, from_date=None, to_date=None):
        """Generate call analytics report"""
        try:
            call_records = self.get_call_records(from_date, to_date, limit=1000)
            
            if not call_records.get('success', True):
                return call_records
            
            results = call_records.get('results', [])
            
            # Calculate analytics
            total_calls = len(results)
            answered_calls = len([r for r in results if r.get('status') == 'answered'])
            missed_calls = len([r for r in results if r.get('status') == 'missed'])
            
            total_duration = sum([r.get('call_duration', 0) for r in results])
            avg_duration = total_duration / total_calls if total_calls > 0 else 0
            
            # Group by date
            daily_stats = {}
            for record in results:
                date = record.get('date', '')
                if date not in daily_stats:
                    daily_stats[date] = {'total': 0, 'answered': 0, 'missed': 0}
                
                daily_stats[date]['total'] += 1
                if record.get('status') == 'answered':
                    daily_stats[date]['answered'] += 1
                elif record.get('status') == 'missed':
                    daily_stats[date]['missed'] += 1
            
            return {
                'success': True,
                'analytics': {
                    'total_calls': total_calls,
                    'answered_calls': answered_calls,
                    'missed_calls': missed_calls,
                    'answer_rate': (answered_calls / total_calls * 100) if total_calls > 0 else 0,
                    'total_duration_minutes': total_duration / 60,
                    'avg_duration_seconds': avg_duration,
                    'daily_stats': daily_stats
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def send_whatsapp_message(self, to_number, message_text):
        """Send WhatsApp message via TATA API"""
        try:
            url = f"{self.whatsapp_url}/v1/{self.phone_number_id}/messages"
            payload = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": "text",
                "text": {"body": message_text}
            }
            
            response = requests.post(url, json=payload, headers=self.get_whatsapp_headers())
            
            if response.status_code == 200:
                return {'success': True, 'data': response.json()}
            return {'success': False, 'error': f'API Error: {response.status_code}'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_whatsapp_messages(self):
        """Get WhatsApp messages"""
        try:
            url = f"{self.whatsapp_url}/v1/{self.phone_number_id}/messages"
            response = requests.get(url, headers=self.get_whatsapp_headers())
            
            if response.status_code == 200:
                return {'success': True, 'data': response.json()}
            return {'success': False, 'error': f'API Error: {response.status_code}'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}