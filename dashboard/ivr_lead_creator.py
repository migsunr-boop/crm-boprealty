"""
IVR Lead Auto-Creation Service
Automatically creates leads from IVR calls with proper classification
"""
import re
from django.db import transaction
from django.utils import timezone
from .models import IVRCallLog, Lead, Project, LeadStage, LeadNote

class IVRLeadCreator:
    """Service to automatically create leads from IVR calls"""
    
    def __init__(self):
        self.setup_lead_stages()
    
    def setup_lead_stages(self):
        """Ensure required lead stages exist"""
        stages = [
            {'name': 'IVR Lead', 'category': 'new', 'color': '#3b82f6'},
            {'name': 'Junk Lead', 'category': 'dead', 'color': '#ef4444'},
            {'name': 'Hot Lead', 'category': 'hot', 'color': '#f59e0b'},
        ]
        
        for stage_data in stages:
            LeadStage.objects.get_or_create(
                name=stage_data['name'],
                defaults={
                    'category': stage_data['category'],
                    'color': stage_data['color'],
                    'order': 0
                }
            )
    
    def clean_phone_number(self, phone):
        """Clean and format phone number"""
        clean_phone = re.sub(r'[^\d+]', '', phone)
        
        if not clean_phone.startswith('+'):
            if clean_phone.startswith('91') and len(clean_phone) == 12:
                clean_phone = '+' + clean_phone
            elif len(clean_phone) == 10:
                clean_phone = '+91' + clean_phone
        
        return clean_phone
    
    def get_project_from_ivr_number(self, ivr_number):
        """Get project based on IVR number called"""
        # Try to find project by IVR number
        project = Project.objects.filter(ivr_number=ivr_number).first()
        
        if not project:
            # Create default project if none found
            project, created = Project.objects.get_or_create(
                name=f"IVR Project ({ivr_number})",
                defaults={
                    'location': 'Unknown',
                    'description': f'Auto-created from IVR number {ivr_number}',
                    'property_type': 'apartment',
                    'bhk_options': '2BHK, 3BHK',
                    'price_min': 1000000,
                    'price_max': 5000000,
                    'created_by_id': 1,
                    'ivr_number': ivr_number
                }
            )
        
        return project
    
    def classify_call_quality(self, call):
        """Classify call as quality lead or junk based on duration"""
        if call.duration == 0:
            return 'junk', 'Missed call - no answer'
        elif call.duration < 60:  # Less than 1 minute
            return 'junk', f'Short call - {call.duration}s duration'
        else:
            return 'quality', f'Good call - {call.duration}s duration'
    
    def create_lead_from_call(self, call):
        """Create lead from IVR call"""
        
        clean_phone = self.clean_phone_number(call.caller_id_number)
        
        # Check if lead already exists for this phone
        existing_lead = Lead.objects.filter(phone=clean_phone).first()
        
        if existing_lead:
            # Update existing lead with new call info
            self.update_existing_lead(existing_lead, call)
            return existing_lead, False
        
        # Get project from IVR number
        project = self.get_project_from_ivr_number(call.call_to_number)
        
        # Classify call quality
        quality, quality_reason = self.classify_call_quality(call)
        
        # Determine lead stage
        if quality == 'junk':
            stage = LeadStage.objects.get(name='Junk Lead')
        else:
            stage = LeadStage.objects.get(name='IVR Lead')
        
        # Create lead
        lead_name = f"IVR Caller {clean_phone[-4:]}"
        
        with transaction.atomic():
            lead = Lead.objects.create(
                name=lead_name,
                email=f"ivr{clean_phone[-4:]}@unknown.com",
                phone=clean_phone,
                source='ivr_call',
                source_details=f"IVR call to {call.call_to_number}",
                current_stage=stage,
                notes=f"Auto-created from IVR call\nCall Duration: {call.duration}s\nQuality: {quality_reason}",
                ip_address=None,
                landing_page=f"IVR:{call.call_to_number}",
                quality_score=8 if quality == 'quality' else 2
            )
            
            # Associate with project
            lead.interested_projects.add(project)
            
            # Link IVR call to lead
            call.associated_lead = lead
            call.processed = True
            call.save()
            
            # Create call note
            LeadNote.objects.create(
                lead=lead,
                call_type='ivr_call',
                call_outcome='interested' if quality == 'quality' else 'no_answer',
                note=f"IVR Call: {call.caller_id_number} to {call.call_to_number}\nDuration: {call.call_duration_formatted}\nProject: {project.name}\nQuality: {quality_reason}",
                call_duration=call.duration,
                created_by_id=1  # System user
            )
        
        return lead, True
    
    def update_existing_lead(self, lead, call):
        """Update existing lead with new IVR call info"""
        
        # Get project from IVR number
        project = self.get_project_from_ivr_number(call.call_to_number)
        
        # Add project to interested projects if not already there
        if not lead.interested_projects.filter(id=project.id).exists():
            lead.interested_projects.add(project)
        
        # Classify new call
        quality, quality_reason = self.classify_call_quality(call)
        
        # Update lead stage if this is a quality call and lead is currently junk
        if quality == 'quality' and lead.current_stage.name == 'Junk Lead':
            ivr_stage = LeadStage.objects.get(name='IVR Lead')
            lead.current_stage = ivr_stage
            lead.quality_score = max(lead.quality_score, 6)
        
        # Add to notes
        lead.notes += f"\n\n[{timezone.now()}] New IVR Call\nProject: {project.name}\nDuration: {call.duration}s\nQuality: {quality_reason}"
        lead.save()
        
        # Link call to lead
        call.associated_lead = lead
        call.processed = True
        call.save()
        
        # Create call note
        LeadNote.objects.create(
            lead=lead,
            call_type='ivr_call',
            call_outcome='interested' if quality == 'quality' else 'no_answer',
            note=f"Follow-up IVR Call: {call.caller_id_number} to {call.call_to_number}\nDuration: {call.call_duration_formatted}\nProject: {project.name}",
            call_duration=call.duration,
            created_by_id=1
        )
    
    def process_unprocessed_calls(self):
        """Process all unprocessed IVR calls and create leads"""
        
        unprocessed_calls = IVRCallLog.objects.filter(processed=False).order_by('-start_stamp')
        
        results = {
            'total_calls': len(unprocessed_calls),
            'new_leads': 0,
            'updated_leads': 0,
            'quality_leads': 0,
            'junk_leads': 0,
            'errors': []
        }
        
        for call in unprocessed_calls:
            try:
                lead, is_new = self.create_lead_from_call(call)
                
                if is_new:
                    results['new_leads'] += 1
                else:
                    results['updated_leads'] += 1
                
                # Count quality vs junk
                if lead.current_stage.name == 'Junk Lead':
                    results['junk_leads'] += 1
                else:
                    results['quality_leads'] += 1
                    
            except Exception as e:
                results['errors'].append(f"Error processing call {call.uuid}: {str(e)}")
        
        return results
    
    def get_lead_statistics(self):
        """Get statistics for IVR-generated leads"""
        
        ivr_leads = Lead.objects.filter(source='ivr_call')
        
        stats = {
            'total_ivr_leads': ivr_leads.count(),
            'quality_leads': ivr_leads.exclude(current_stage__name='Junk Lead').count(),
            'junk_leads': ivr_leads.filter(current_stage__name='Junk Lead').count(),
            'by_project': {},
            'recent_leads': ivr_leads.order_by('-created_at')[:10]
        }
        
        # Group by project
        for lead in ivr_leads:
            for project in lead.interested_projects.all():
                if project.name not in stats['by_project']:
                    stats['by_project'][project.name] = {'total': 0, 'quality': 0, 'junk': 0}
                
                stats['by_project'][project.name]['total'] += 1
                
                if lead.current_stage.name == 'Junk Lead':
                    stats['by_project'][project.name]['junk'] += 1
                else:
                    stats['by_project'][project.name]['quality'] += 1
        
        return stats