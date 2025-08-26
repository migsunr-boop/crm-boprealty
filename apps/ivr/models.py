from django.db import models
from django.utils import timezone
from dashboard.models import Lead, Project

class IVRCall(models.Model):
    STATUS_CHOICES = [
        ('answered', 'Answered'),
        ('missed', 'Missed'),
    ]
    
    phone_number = models.CharField(max_length=20)
    project_name = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(default=timezone.now)
    
    # Link to existing models
    lead = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'ivr_calls'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.phone_number} - {self.project_name} - {self.status}"