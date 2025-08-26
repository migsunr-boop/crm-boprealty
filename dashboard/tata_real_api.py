"""
Real TATA API Integration - No Sample Data
"""
import requests
from django.conf import settings

class TATARealAPI:
    def __init__(self):
        self.token = getattr(settings, 'TATA_AUTH_TOKEN', '')
        self.base_url = 'https://api-smartflo.tatateleservices.com/v1'
        
    def get_real_call_records(self):
        """Get actual call records from TATA API"""
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        try:
            # Try CDR endpoint
            response = requests.get(f'{self.base_url}/cdr', headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                return data.get('records', data.get('data', []))
                
            # Try call-logs endpoint  
            response = requests.get(f'{self.base_url}/call-logs', headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                return data.get('calls', data.get('data', []))
                
        except Exception as e:
            print(f"TATA API Error: {e}")
            
        return []
    
    def get_departments(self):
        """Get real departments from TATA"""
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(f'{self.base_url}/departments', headers=headers, timeout=15)
            if response.status_code == 200:
                return response.json().get('departments', [])
        except:
            pass
            
        return []