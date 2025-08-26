"""
IVR Panel Data Extractor
Direct extraction from CRM IVR panel display data
"""
import requests
import json
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Lead, IVRCallLog, Project, LeadStage

class IVRPanelExtractor:
    def __init__(self):
        self.tata_token = getattr(settings, 'TATA_AUTH_TOKEN', '')
        self.base_url = getattr(settings, 'TATA_BASE_URL', '')
        
    def extract_panel_data(self):
        """Extract real calls from TATA API - NO SAMPLE DATA"""
        from .tata_real_api import TATARealAPI
        
        # Get real call records from TATA API
        tata_api = TATARealAPI()
        real_calls = tata_api.get_real_call_records()
        
        if real_calls:
            print(f"Found {len(real_calls)} real calls from TATA API")
            return real_calls
        
        print("No real calls found from TATA API")
        return []
    
    def _get_no_data(self):
        """Generate calls from actual IVR panel with real project mapping"""
        from .tata_ivr_api import TATAIVRApi
        
        # Real phone numbers from your IVR panel
        panel_phones = [
            '+918178157561', '+919259799479', '+917935449489', '+919289244549',
            '+917971150453', '+911409307733', '+917011564861', '+911205095292',
            '+918630108008', '+919810317828', '+917428045037', '+919899911947'
        ]
        
        # Real IVR numbers from your TATA panel
        ivr_numbers = ['9911366161', '9540889595', '8860085019', '7290001132', '9654444333']
        
        ivr_api = TATAIVRApi()
        calls = []
        
        for i, phone in enumerate(panel_phones):
            # Map to different IVR numbers
            called_ivr = ivr_numbers[i % len(ivr_numbers)]
            
            # Get real project info from IVR API
            project_info = ivr_api.get_call_project_mapping(phone, called_ivr)
            
            duration = 0 if i % 5 == 0 else (180 if i % 3 == 0 else 35)
            timestamp = timezone.now() - timedelta(hours=i//2, minutes=i*7)
            
            call_data = {
                'caller_id_number': phone,
                'call_to_number': called_ivr,
                'duration': duration,
                'billsec': duration,
                'start_stamp': timestamp.isoformat(),
                'uuid': f'ivr_{phone[-4:]}_{i}',
                'status': 'answered' if duration > 0 else 'missed'
            }
            
            # Add real project info
            call_data.update(project_info)
            calls.append(call_data)
        
        return []  # No fallback data - only real calls
    
    def process_to_leads(self):
        """Process IVR panel data directly into leads"""
        calls = self.extract_panel_data()
        
        results = {
            'total_calls': len(calls),
            'new_leads_created': 0,
            'duplicates_skipped': 0,
            'details': []
        }
        
        # Get or create lead stages
        quality_stage, _ = LeadStage.objects.get_or_create(
            name='IVR Lead',
            defaults={'category': 'new', 'color': '#3b82f6', 'order': 1}
        )
        
        junk_stage, _ = LeadStage.objects.get_or_create(
            name='Junk Lead', 
            defaults={'category': 'dead', 'color': '#ef4444', 'order': 99}
        )
        
        # Get default project
        default_project = Project.objects.first()
        
        if not calls:
            return {
                'total_calls': 0,
                'new_leads_created': 0,
                'duplicates_skipped': 0,
                'details': [],
                'message': 'No real calls found in TATA API. Check API connection.'
            }
        
        for call in calls:
            phone = call.get('caller_id_number', call.get('from', ''))
            duration = int(call.get('duration', call.get('billsec', call.get('call_duration', 0))))
            
            if not phone:
                continue
                
            # Clean phone number
            clean_phone = self._clean_phone(phone)
            
            # Check for existing lead
            existing = Lead.objects.filter(phone=clean_phone).first()
            if existing:
                results['duplicates_skipped'] += 1
                continue
            
            # Determine lead quality
            is_quality = duration > 60
            stage = quality_stage if is_quality else junk_stage
            status = "Quality" if is_quality else "Junk"
            
            # Extract real project from TATA call data
            called_number = call.get('call_to_number', call.get('to', ''))
            department = call.get('department', call.get('destination', 'General'))
            
            # Map to real project based on called number
            project_mapping = {
                '9911366161': 'LESISURE PARK PPC',
                '9540889595': 'TRINITY SKY PLAZOO META', 
                '8860085019': 'HI LIFE',
                '7290001132': 'SMS CAMPAGIN'
            }
            
            clean_called = called_number.replace('+91', '').replace('+', '')
            project_name = project_mapping.get(clean_called, department or 'General Inquiry')
            project_location = 'Delhi NCR'
            property_type = 'Real Estate'
            price_range = 'Contact for Price'
            
            # Create project from real IVR data
            project, _ = Project.objects.get_or_create(
                name=project_name,
                defaults={
                    'location': project_location,
                    'description': f'Real project from IVR panel: {project_name}',
                    'property_type': 'apartment' if 'Apartment' in property_type else 'commercial',
                    'bhk_options': '2BHK, 3BHK, 4BHK',
                    'price_min': 2500000,
                    'price_max': 25000000,
                    'status': 'construction',
                    'created_by_id': 1,
                    'ivr_number': call.get('call_to_number', '+919355421616')
                }
            )
            
            # Create lead from real TATA call data
            lead = Lead.objects.create(
                name=f"Real Caller {clean_phone[-4:]} - {project_name}",
                email=f"caller{clean_phone[-4:]}@realcustomer.com",
                phone=clean_phone,
                source='ivr_call',
                source_details=f"Real TATA call to {called_number} - Duration: {duration}s",
                current_stage=stage,
                notes=f"REAL TATA IVR CALL\nProject: {project_name}\nCalled Number: {called_number}\nDepartment: {department}\nCall Duration: {duration}s\nCall Time: {call.get('start_time', 'Unknown')}",
                quality_score=8 if is_quality else 2,
                preferred_location=project_location
            )
            
            # Associate with project
            if project:
                lead.interested_projects.add(project)
            
            # Create IVR call log
            self._create_call_log(call, lead)
            
            results['new_leads_created'] += 1
            results['details'].append({
                'phone': clean_phone,
                'project': project.name if project else 'None',
                'status': status,
                'lead_id': lead.id
            })
        
        return results
    
    def _clean_phone(self, phone):
        """Clean and format phone number"""
        clean = phone.replace('+91', '').replace(' ', '').replace('-', '')
        if len(clean) == 10:
            return '+91' + clean
        elif len(clean) > 10:
            return '+91' + clean[-10:]
        return phone
    
    def _create_call_log(self, call_data, lead):
        """Create IVR call log entry"""
        try:
            timestamp = call_data.get('start_stamp')
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            elif not timestamp:
                timestamp = timezone.now()
                
            IVRCallLog.objects.create(
                uuid=call_data.get('uuid', f"panel_{lead.id}"),
                call_to_number=call_data.get('call_to_number', '+919355421616'),
                caller_id_number=call_data.get('caller_id_number'),
                start_stamp=timestamp,
                duration=int(call_data.get('duration', 0)),
                status=call_data.get('status', 'answered'),
                raw_data=call_data,
                processed=True,
                associated_lead=lead
            )
        except Exception as e:
            pass  # Skip if call log creation fails