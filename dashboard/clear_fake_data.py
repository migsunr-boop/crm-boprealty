"""
Clear fake IVR data and create fresh leads with real project names
"""
from .models import Lead, IVRCallLog, Project

def clear_fake_ivr_data():
    """Remove all fake IVR leads and projects"""
    # Delete fake IVR leads
    Lead.objects.filter(source='ivr_call').delete()
    
    # Delete fake IVR call logs
    IVRCallLog.objects.all().delete()
    
    # Delete fake projects
    fake_projects = ['Godrej Woods', 'Skyline Phoenix', 'Green Valley Apartments', 
                    'Metro Heights', 'Royal Gardens', 'Urban Vista']
    Project.objects.filter(name__in=fake_projects).delete()
    
    return "Cleared all fake IVR data"