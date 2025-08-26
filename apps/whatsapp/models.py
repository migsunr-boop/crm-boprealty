from django.db import models
from django.utils import timezone

class WhatsAppMessageLog(models.Model):
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('failed', 'Failed'),
    ]
    
    phone = models.CharField(max_length=20)
    template_name = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='queued')
    error_code = models.CharField(max_length=50, blank=True)
    message_id = models.CharField(max_length=100, blank=True)
    
    # Webhook tracking
    webhook_payload = models.JSONField(null=True, blank=True)
    
    timestamp = models.DateTimeField(default=timezone.now)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.phone} - {self.template_name} - {self.status}"