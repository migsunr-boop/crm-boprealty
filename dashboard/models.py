from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import os
from datetime import time, datetime, timedelta
from django.db.models import Q, Count, Case, When, FloatField, F, ExpressionWrapper, fields
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import json

def project_image_upload_path(instance, filename):
    """Generate upload path for project images"""
    return f'projects/{instance.id}/{filename}'

class Project(models.Model):
    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('construction', 'Under Construction'),
        ('completed', 'Completed'),
        ('featured', 'Featured'),
        ('sold_out', 'Sold Out'),
    ]
    
    PROPERTY_TYPES = [
        ('apartment', 'Apartment'),
        ('villa', 'Villa'),
        ('plot', 'Plot'),
        ('commercial', 'Commercial'),
        ('warehouse', 'Warehouse'),
        ('office', 'Office Space'),
    ]
    
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    city = models.CharField(max_length=100, default='')
    state = models.CharField(max_length=100, default='')
    pincode = models.CharField(max_length=10, default='')
    description = models.TextField()
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPES, default='apartment')
    bhk_options = models.CharField(max_length=100, help_text="e.g., 1BHK, 2BHK, 3BHK")
    price_min = models.DecimalField(max_digits=12, decimal_places=2)
    price_max = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    
    # Enhanced property details
    area_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Minimum area in sq ft")
    area_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Maximum area in sq ft")
    total_units = models.PositiveIntegerField(null=True, blank=True)
    available_units = models.PositiveIntegerField(null=True, blank=True)
    possession_date = models.DateField(null=True, blank=True)
    
    # Virtual tour and media
    virtual_tour_url = models.URLField(blank=True, help_text="360° virtual tour link")
    video_url = models.URLField(blank=True, help_text="Property video link")
    brochure_pdf = models.FileField(upload_to='brochures/', null=True, blank=True)
    
    # Image fields
    main_image = models.ImageField(upload_to='projects/', null=True, blank=True)
    floor_plan = models.ImageField(upload_to='projects/', null=True, blank=True)
    
    # Amenities and features
    amenities = models.TextField(blank=True, help_text="List amenities separated by commas")
    features = models.TextField(blank=True, help_text="List key features separated by commas")
    
    # Location advantages
    nearby_schools = models.TextField(blank=True)
    nearby_hospitals = models.TextField(blank=True)
    nearby_malls = models.TextField(blank=True)
    transportation = models.TextField(blank=True)
    
    # Developer and contact info
    developer_name = models.CharField(max_length=255, blank=True)
    contact_person = models.CharField(max_length=255, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)
    ivr_number = models.CharField(max_length=20, blank=True, help_text="IVR Number for this project")

    # RERA and legal
    rera_number = models.CharField(max_length=100, blank=True)
    approval_status = models.CharField(max_length=100, blank=True)
    
    # Meta fields
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_projects')
    
    def __str__(self):
        return self.name
    
    @property
    def sold_percentage(self):
        if self.total_units and self.available_units is not None and self.total_units > 0:
            sold = self.total_units - self.available_units
            return (sold / self.total_units) * 100
        return 0

    @property
    def conversion_rate(self):
        total_leads = self.interested_leads.count()
        if total_leads == 0:
            return 0
        converted_leads = self.interested_leads.filter(current_stage__category='closed').count()
        return (converted_leads / total_leads) * 100
    
    class Meta:
        ordering = ['-created_at']

class ProjectUnit(models.Model):
    UNIT_STATUS_CHOICES = [
        ('available', 'Available'),
        ('booked', 'Booked'),
        ('sold', 'Sold'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='units')
    unit_number = models.CharField(max_length=50)
    floor = models.PositiveIntegerField()
    size = models.DecimalField(max_digits=10, decimal_places=2, help_text="Size in sq ft")
    price = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=UNIT_STATUS_CHOICES, default='available')

    def __str__(self):
        return f"{self.project.name} - Unit {self.unit_number}"

    class Meta:
        unique_together = ('project', 'unit_number')
        ordering = ['floor', 'unit_number']

class ProjectImage(models.Model):
    """Additional images for projects"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='projects/')
    caption = models.CharField(max_length=255, blank=True)
    is_featured = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.project.name} - {self.caption or 'Image'}"
    
    class Meta:
        ordering = ['-is_featured', '-uploaded_at']

# Enhanced Lead Stage System
class LeadStage(models.Model):
    """Lead stages for tracking lead journey"""
    STAGE_CATEGORIES = [
        ('new', 'New'),
        ('hot', 'Hot'),
        ('warm', 'Warm'),
        ('cold', 'Cold'),
        ('closed', 'Closed'),
        ('dead', 'Dead/Junk'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=20, choices=STAGE_CATEGORIES)
    order = models.PositiveIntegerField(default=0)
    color = models.CharField(max_length=7, default='#6b7280')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    # Stage behavior settings
    auto_progress_days = models.PositiveIntegerField(null=True, blank=True, help_text="Auto progress after X days")
    requires_action = models.BooleanField(default=False, help_text="Requires manual action to progress")
    is_final_stage = models.BooleanField(default=False, help_text="Final stage in journey")
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['category', 'order']

# Enhanced Lead Model with Advanced Tracking
class Lead(models.Model):
    SOURCE_CHOICES = [
        ('website', 'Website'),
        ('google_ppc', 'Google PPC'),
        ('google_performance_max', 'Google Performance Max'),
        ('google_discovery', 'Google Discovery'),
        ('google_display', 'Google Display'),
        ('google_demand_gen', 'Google Demand Generation'),
        ('facebook_ads', 'Facebook Ads'),
        ('facebook_organic', 'Facebook Organic'),
        ('instagram_ads', 'Instagram Ads'),
        ('linkedin_ads', 'LinkedIn Ads'),
        ('referral', 'Referral'),
        ('walk_in', 'Walk In'),
        ('phone_call', 'Phone Call'),
        ('ivr_call', 'IVR Call'),
        ('whatsapp', 'WhatsApp'),
        ('email_campaign', 'Email Campaign'),
        ('sms_campaign', 'SMS Campaign'),
        ('other', 'Other'),
    ]
    
    INDUSTRY_CHOICES = [
        ('it', 'Information Technology'),
        ('finance', 'Finance & Banking'),
        ('healthcare', 'Healthcare'),
        ('education', 'Education'),
        ('manufacturing', 'Manufacturing'),
        ('retail', 'Retail'),
        ('real_estate', 'Real Estate'),
        ('government', 'Government'),
        ('startup', 'Startup'),
        ('other', 'Other'),
    ]
    
    JOB_FUNCTION_CHOICES = [
        ('ceo', 'CEO/Founder'),
        ('cto', 'CTO'),
        ('manager', 'Manager'),
        ('director', 'Director'),
        ('executive', 'Executive'),
        ('consultant', 'Consultant'),
        ('entrepreneur', 'Entrepreneur'),
        ('employee', 'Employee'),
        ('student', 'Student'),
        ('retired', 'Retired'),
        ('other', 'Other'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    
    # Alternative Contact Information
    alternative_phone = models.CharField(max_length=20, blank=True)
    alternative_email = models.EmailField(blank=True)
    alternative_contact_person = models.CharField(max_length=255, blank=True)
    
    # Lead Source and Tracking
    source = models.CharField(max_length=30, choices=SOURCE_CHOICES)
    source_details = models.TextField(blank=True, help_text="Campaign details, creative info, etc.")
    utm_source = models.CharField(max_length=100, blank=True)
    utm_medium = models.CharField(max_length=100, blank=True)
    utm_campaign = models.CharField(max_length=100, blank=True)
    utm_content = models.CharField(max_length=100, blank=True)
    utm_term = models.CharField(max_length=100, blank=True)
    
    # Technical Tracking
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    referrer_url = models.URLField(blank=True)
    landing_page = models.URLField(blank=True)
    
    # Lead Stage and Status
    current_stage = models.ForeignKey(LeadStage, on_delete=models.SET_NULL, null=True, related_name='leads')
    previous_stage = models.ForeignKey(LeadStage, on_delete=models.SET_NULL, null=True, blank=True, related_name='previous_leads')
    stage_changed_at = models.DateTimeField(auto_now_add=True)
    
    # Lead Classification
    is_recapture = models.BooleanField(default=False, help_text="Lead from multiple sources")
    recapture_count = models.PositiveIntegerField(default=0)
    quality_score = models.PositiveIntegerField(default=0, help_text="Lead quality score 1-10")
    
    # Buyer Persona Information
    budget_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    budget_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    preferred_location = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    
    # Professional Information
    industry = models.CharField(max_length=20, choices=INDUSTRY_CHOICES, blank=True)
    job_function = models.CharField(max_length=20, choices=JOB_FUNCTION_CHOICES, blank=True)
    company_name = models.CharField(max_length=255, blank=True)
    annual_income = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Pain Points and Goals
    pain_points = models.TextField(blank=True)
    goals_objectives = models.TextField(blank=True)
    timeline = models.CharField(max_length=100, blank=True, help_text="When planning to buy")
    
    # Lead Management
    notes = models.TextField(blank=True, help_text="General notes and remarks")
    interested_projects = models.ManyToManyField(Project, blank=True, related_name='interested_leads')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_leads')
    sticky_agent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sticky_leads', help_text="Agent who first handled this lead")
    
    # Follow-up Information
    follow_up_date = models.DateField(null=True, blank=True)
    last_contact_date = models.DateField(null=True, blank=True)
    next_action = models.CharField(max_length=255, blank=True)
    requires_callback = models.BooleanField(default=False)
    callback_time = models.DateTimeField(null=True, blank=True)
    
    # Duplicate Management
    is_duplicate = models.BooleanField(default=False)
    original_lead = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.current_stage.name if self.current_stage else 'No Stage'}"
    
    def move_to_stage(self, new_stage, user=None, notes=''):
        """Move lead to a new stage with tracking"""
        if self.current_stage != new_stage:
            # Create stage history entry
            LeadStageHistory.objects.create(
                lead=self,
                from_stage=self.current_stage,
                to_stage=new_stage,
                changed_by=user,
                notes=notes
            )
            
            self.previous_stage = self.current_stage
            self.current_stage = new_stage
            self.stage_changed_at = timezone.now()
            self.save()
    
    def check_recapture(self):
        """Check if this is a recapture lead"""
        existing_leads = Lead.objects.filter(
            Q(email=self.email) | Q(phone=self.phone)
        ).exclude(id=self.id)
        
        if existing_leads.exists():
            self.is_recapture = True
            self.recapture_count = existing_leads.count()
            
            # Assign to sticky agent if exists
            first_lead = existing_leads.first()
            if first_lead.sticky_agent:
                self.assigned_to = first_lead.sticky_agent
            elif first_lead.assigned_to:
                self.sticky_agent = first_lead.assigned_to
                self.assigned_to = first_lead.assigned_to
            
            self.save()
    
    @property
    def is_overdue_followup(self):
        """Check if follow-up is overdue"""
        if self.follow_up_date and self.follow_up_date < timezone.now().date():
            return True
        return False
    
    @property
    def days_since_last_contact(self):
        """Days since last contact"""
        if self.last_contact_date:
            return (timezone.now().date() - self.last_contact_date).days
        return (timezone.now().date() - self.created_at.date()).days
    
    class Meta:
        ordering = ['-created_at']

class Client(models.Model):
    SOURCE_CHOICES = [
        ('internal', 'Internal'),
        ('external', 'External'),
    ]
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, unique=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    access_rights = models.TextField(blank=True, help_text="Describe access rights for this client")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_clients')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-created_at']

class LeadStageHistory(models.Model):
    """Track lead stage changes"""
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='stage_history')
    from_stage = models.ForeignKey(LeadStage, on_delete=models.SET_NULL, null=True, blank=True, related_name='from_history')
    to_stage = models.ForeignKey(LeadStage, on_delete=models.SET_NULL, null=True, related_name='to_history')
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    duration_in_previous_stage = models.PositiveIntegerField(null=True, blank=True, help_text="Days in previous stage")
    
    def save(self, *args, **kwargs):
        # Calculate duration in previous stage
        if self.from_stage and self.lead.stage_changed_at:
            duration = timezone.now() - self.lead.stage_changed_at
            self.duration_in_previous_stage = duration.days
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.lead.name}: {self.from_stage} → {self.to_stage}"
    
    class Meta:
        ordering = ['-changed_at']

class LeadNote(models.Model):
    """Enhanced call notes and interactions"""
    CALL_TYPES = [
        ('outgoing', 'Outgoing Call'),
        ('incoming', 'Incoming Call'),
        ('ivr_call', 'IVR Call'),
        ('missed_call', 'Missed Call'),
        ('meeting', 'Meeting'),
        ('site_visit', 'Site Visit'),
        ('virtual_meet', 'Virtual Meeting'),
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
        ('sms', 'SMS'),
        ('other', 'Other'),
    ]
    
    CALL_OUTCOMES = [
        ('interested', 'Interested'),
        ('not_interested', 'Not Interested'),
        ('callback_requested', 'Callback Requested'),
        ('no_answer', 'No Answer'),
        ('busy', 'Busy'),
        ('wrong_number', 'Wrong Number'),
        ('site_visit_scheduled', 'Site Visit Scheduled'),
        ('virtual_meet_scheduled', 'Virtual Meeting Scheduled'),
        ('negotiation', 'In Negotiation'),
        ('deal_closed', 'Deal Closed'),
        ('follow_up_later', 'Follow Up Later'),
    ]
    
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='call_notes')
    call_type = models.CharField(max_length=20, choices=CALL_TYPES, default='outgoing')
    call_outcome = models.CharField(max_length=30, choices=CALL_OUTCOMES, blank=True)
    note = models.TextField(help_text="Detailed conversation notes")
    next_action = models.CharField(max_length=255, blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    
    # Call details
    call_duration = models.PositiveIntegerField(null=True, blank=True, help_text="Duration in seconds")
    call_recording_url = models.URLField(blank=True)
    
    # Meeting details
    meeting_location = models.CharField(max_length=255, blank=True)
    meeting_attendees = models.ManyToManyField(User, blank=True, related_name='attended_meetings')
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.lead.name} - {self.get_call_type_display()} - {self.created_at.strftime('%d %b %Y')}"
    
    class Meta:
        ordering = ['-created_at']

# WhatsApp Automation System
class WhatsAppTemplate(models.Model):
    """WhatsApp message templates for automation"""
    TEMPLATE_STAGES = [
        ('stage_1_landing', 'Stage 1 - Call Landing'),
        ('stage_2_interested', 'Stage 2 - Interested Call'),
        ('stage_3_not_picking', 'Stage 3 - Not Picking Up'),
        ('stage_4_missed_ivr', 'Stage 4 - Missed IVR'),
        ('stage_5_site_visit', 'Stage 5 - Site Visit/Meeting'),
        ('stage_6_day_7', 'Stage 6 - Day 7 Follow-up'),
        ('stage_7_day_15', 'Stage 7 - Day 15 Follow-up'),
        ('stage_8_day_30', 'Stage 8 - Day 30 Follow-up'),
    ]
    
    name = models.CharField(max_length=100)
    stage = models.CharField(max_length=30, choices=TEMPLATE_STAGES, unique=True)
    message_template = models.TextField(help_text="Use {name}, {project_name}, {number} as placeholders")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.get_stage_display()}"
    
    def render_message(self, lead, project=None, additional_context=None):
        """Render template with lead data"""
        context = {
            'name': lead.name,
            'project_name': project.name if project else 'our projects',
            'number': '+91-XXXXXXXXXX',  # Replace with actual number
        }
        
        if additional_context:
            context.update(additional_context)
        
        message = self.message_template
        for key, value in context.items():
            message = message.replace(f'{{{key}}}', str(value))
        
        return message

class WhatsAppMessage(models.Model):
    """Track WhatsApp messages sent"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('failed', 'Failed'),
    ]
    
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='whatsapp_messages')
    template = models.ForeignKey(WhatsAppTemplate, on_delete=models.SET_NULL, null=True)
    message_content = models.TextField()
    phone_number = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # WhatsApp API response
    message_id = models.CharField(max_length=100, blank=True)
    api_response = models.JSONField(null=True, blank=True)
    
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"WhatsApp to {self.lead.name} - {self.status}"
    
    class Meta:
        ordering = ['-created_at']

class IVRCallLog(models.Model):
    CALL_STATUS_CHOICES = [
        ('received', 'Received'),
        ('answered', 'Answered'),
        ('ended', 'Ended'),
        ('failed', 'Failed'),
        ('busy', 'Busy'),
        ('no_answer', 'No Answer'),
    ]
    
    # Call identification
    uuid = models.CharField(max_length=100, unique=True)
    call_to_number = models.CharField(max_length=20)
    caller_id_number = models.CharField(max_length=20)
    call_id = models.CharField(max_length=100, blank=True)
    
    # Call timing
    start_stamp = models.DateTimeField()
    end_stamp = models.DateTimeField(null=True, blank=True)
    duration = models.PositiveIntegerField(default=0, help_text="Duration in seconds")
    status = models.CharField(max_length=20, choices=CALL_STATUS_CHOICES, default='received')
    
    # Location and billing
    billing_circle = models.CharField(max_length=50, blank=True)
    customer_no_with_prefix = models.CharField(max_length=30, blank=True)
    
    # Raw data and associations
    raw_data = models.JSONField()
    associated_lead = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name='ivr_calls')
    
    # Processing
    created_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    
    @property
    def call_duration_formatted(self):
        if self.duration:
            minutes = self.duration // 60
            seconds = self.duration % 60
            return f"{minutes}m {seconds}s"
        return "0s"
    
    def associate_with_lead(self):
        """Associate call with existing lead"""
        if not self.associated_lead:
            clean_caller = self.caller_id_number.replace('+91', '').replace(' ', '').replace('-', '')
            
            lead = Lead.objects.filter(
                Q(phone__icontains=clean_caller[-10:])
            ).first()
            
            if lead:
                self.associated_lead = lead
                self.save()
                
                # Create call note
                LeadNote.objects.create(
                    lead=lead,
                    call_type='ivr_call',
                    note=f"IVR Call: {self.caller_id_number} to {self.call_to_number}. Duration: {self.call_duration_formatted}",
                    call_duration=self.duration,
                    created_by_id=1  # System user
                )
                return True
        return False
    
    def __str__(self):
        return f"Call {self.uuid} - {self.caller_id_number}"
    
    class Meta:
        ordering = ['-start_stamp']

class TeamMember(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('team_lead', 'Team Lead'),
        ('senior_sales_executive', 'Senior Sales Executive'),
        ('sales_executive', 'Sales Executive'),
        ('marketing_executive', 'Marketing Executive'),
        ('telecaller', 'Telecaller'),
        ('intern', 'Intern'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    joining_date = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    
    # Performance tracking
    target_leads_monthly = models.PositiveIntegerField(default=0)
    target_site_visits_monthly = models.PositiveIntegerField(default=0)
    target_closures_monthly = models.PositiveIntegerField(default=0)
    
    # Permissions
    can_access_dashboard = models.BooleanField(default=True)
    can_access_projects = models.BooleanField(default=True)
    can_access_leads = models.BooleanField(default=True)
    can_access_reports = models.BooleanField(default=False)
    can_access_earnings = models.BooleanField(default=False)
    can_access_clients = models.BooleanField(default=True)
    can_access_calendar = models.BooleanField(default=True)
    can_access_tasks = models.BooleanField(default=True)
    can_access_analytics = models.BooleanField(default=False)
    
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='team_members')
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()}"
    
    @property
    def monthly_performance(self):
        """Get current month performance"""
        from django.db.models import Count, Sum
        current_month = timezone.now().month
        current_year = timezone.now().year
        
        leads_assigned = Lead.objects.filter(
            assigned_to=self.user,
            created_at__month=current_month,
            created_at__year=current_year
        ).count()
        
        site_visits = LeadNote.objects.filter(
            created_by=self.user,
            call_type='site_visit',
            created_at__month=current_month,
            created_at__year=current_year
        ).count()
        
        closures = Lead.objects.filter(
            assigned_to=self.user,
            current_stage__name='Deal Closed',
            updated_at__month=current_month,
            updated_at__year=current_year
        ).count()
        
        return {
            'leads': leads_assigned,
            'site_visits': site_visits,
            'closures': closures,
            'lead_target_percentage': (leads_assigned / self.target_leads_monthly * 100) if self.target_leads_monthly else 0,
            'site_visit_percentage': (site_visits / self.target_site_visits_monthly * 100) if self.target_site_visits_monthly else 0,
            'closure_percentage': (closures / self.target_closures_monthly * 100) if self.target_closures_monthly else 0,
        }
    
    @property
    def leave_balance(self):
        """Get current leave balance"""
        current_year = timezone.now().year
        
        # Default leave types if none exist
        default_balance = {
            'annual_leave': {'allowed': 12, 'used': 0, 'remaining': 12},
            'sick_leave': {'allowed': 8, 'used': 0, 'remaining': 8},
            'casual_leave': {'allowed': 6, 'used': 0, 'remaining': 6}
        }
        
        try:
            from .models import LeaveType, LeaveApplication
            # Get all leave types
            leave_types = LeaveType.objects.all()
            balance = {}
            
            for leave_type in leave_types:
                # Calculate used leaves this year
                used_leaves = LeaveApplication.objects.filter(
                    employee=self.user,
                    leave_type=leave_type,
                    status='approved',
                    from_date__year=current_year
                ).aggregate(total=Sum('days_requested'))['total'] or 0
                
                balance[leave_type.name.lower().replace(' ', '_')] = {
                    'allowed': leave_type.days_allowed_per_year,
                    'used': used_leaves,
                    'remaining': leave_type.days_allowed_per_year - used_leaves
                }
            
            return balance if balance else default_balance
        except:
            return default_balance
    
    @property
    def compoff_balance(self):
        """Get comp-off balance"""
        current_year = timezone.now().year
        
        try:
            from .models import CompOffRequest
            # Approved comp-offs earned
            earned = CompOffRequest.objects.filter(
                employee=self.user,
                status='approved',
                worked_date__year=current_year
            ).count()
            
            # Comp-offs used (attendance marked as comp_off)
            used = Attendance.objects.filter(
                employee=self.user,
                status='comp_off',
                date__year=current_year
            ).count()
            
            return {
                'earned': earned,
                'used': used,
                'remaining': earned - used
            }
        except:
            return {'earned': 0, 'used': 0, 'remaining': 0}
    
    class Meta:
        ordering = ['user__first_name', 'user__last_name']

# Events and Campaign Management
class Event(models.Model):
    EVENT_TYPES = [
        ('property_launch', 'Property Launch'),
        ('open_house', 'Open House'),
        ('seminar', 'Seminar'),
        ('exhibition', 'Exhibition'),
        ('webinar', 'Webinar'),
        ('site_visit', 'Group Site Visit'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=255)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    description = models.TextField()
    
    # Event details
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    location = models.CharField(max_length=255)
    venue_address = models.TextField()
    
    # Registration and capacity
    max_capacity = models.PositiveIntegerField(null=True, blank=True)
    registration_required = models.BooleanField(default=True)
    registration_deadline = models.DateTimeField(null=True, blank=True)
    
    # Associated projects - Fixed related_name
    featured_projects = models.ManyToManyField(Project, blank=True, related_name='featured_events')
    
    # Event management - Fixed related_name
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_campaign_events')
    team_members = models.ManyToManyField(TeamMember, blank=True, related_name='assigned_events')
    
    # Status
    is_active = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.start_date.strftime('%d %b %Y')}"
    
    @property
    def registration_count(self):
        return self.registrations.count()
    
    @property
    def is_full(self):
        if self.max_capacity:
            return self.registration_count >= self.max_capacity
        return False
    
    class Meta:
        ordering = ['-start_date']

class EventRegistration(models.Model):
    """Event registration tracking"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='event_registrations')
    
    # Registration details
    registered_at = models.DateTimeField(auto_now_add=True)
    attended = models.BooleanField(default=False)
    attended_at = models.DateTimeField(null=True, blank=True)
    
    # Follow-up
    follow_up_required = models.BooleanField(default=True)
    follow_up_completed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.lead.name} - {self.event.name}"
    
    class Meta:
        unique_together = ['event', 'lead']
        ordering = ['-registered_at']

# Analytics and Reporting Models
class LeadSource(models.Model):
    """Track lead sources with detailed analytics"""
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50)  # 'paid', 'organic', 'referral', etc.
    cost_per_lead = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    monthly_budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Tracking URLs
    tracking_url = models.URLField(blank=True)
    utm_parameters = models.JSONField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    @property
    def monthly_leads(self):
        current_month = timezone.now().month
        current_year = timezone.now().year
        return Lead.objects.filter(
            source=self.name.lower().replace(' ', '_'),
            created_at__month=current_month,
            created_at__year=current_year
        ).count()
    
    @property
    def conversion_rate(self):
        total_leads = Lead.objects.filter(source=self.name.lower().replace(' ', '_')).count()
        converted_leads = Lead.objects.filter(
            source=self.name.lower().replace(' ', '_'),
            current_stage__name='Deal Closed'
        ).count()
        
        if total_leads > 0:
            return (converted_leads / total_leads) * 100
        return 0

# Expense and CPL Tracking
class MarketingExpense(models.Model):
    """Track marketing expenses for CPL calculation"""
    EXPENSE_CATEGORIES = [
        ('google_ads', 'Google Ads'),
        ('facebook_ads', 'Facebook Ads'),
        ('linkedin_ads', 'LinkedIn Ads'),
        ('print_media', 'Print Media'),
        ('radio', 'Radio'),
        ('tv', 'Television'),
        ('outdoor', 'Outdoor Advertising'),
        ('events', 'Events & Exhibitions'),
        ('content_marketing', 'Content Marketing'),
        ('seo', 'SEO Services'),
        ('other', 'Other'),
    ]
    
    category = models.CharField(max_length=20, choices=EXPENSE_CATEGORIES)
    campaign_name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    
    # Campaign details
    description = models.TextField(blank=True)
    vendor = models.CharField(max_length=255, blank=True)
    invoice_number = models.CharField(max_length=100, blank=True)
    
    # Tracking
    leads_generated = models.PositiveIntegerField(default=0)
    cost_per_lead = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if self.leads_generated > 0:
            self.cost_per_lead = self.amount / self.leads_generated
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.campaign_name} - ₹{self.amount}"
    
    class Meta:
        ordering = ['-date']

class Meeting(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='meetings')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True)
    meeting_date = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    attendees = models.ManyToManyField(User, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_meetings')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Meeting with {self.lead.name} on {self.meeting_date.strftime('%d %b %Y')}"
    
    class Meta:
        ordering = ['-meeting_date']

class Earning(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, null=True, blank=True)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_earned = models.DateField()
    earned_by = models.ForeignKey(User, on_delete=models.CASCADE)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"₹{self.commission_amount} - {self.project.name}"
    
    class Meta:
        ordering = ['-date_earned']

# Calendar Event - Fixed related_name conflicts
class CalendarEvent(models.Model):
    EVENT_TYPES = [
        ('meeting', 'Meeting'),
        ('site_visit', 'Site Visit'),
        ('follow_up', 'Follow Up'),
        ('team_meeting', 'Team Meeting'),
        ('training', 'Training'),
        ('birthday', 'Birthday'),
        ('anniversary', 'Anniversary'),
        ('other', 'Other'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, default='meeting')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    all_day = models.BooleanField(default=False)
    location = models.CharField(max_length=255, blank=True)
    color = models.CharField(max_length=7, default='#4f46e5')
    
    # Fixed related_name conflicts
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True, related_name='calendar_events')
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, null=True, blank=True, related_name='calendar_events')
    attendees = models.ManyToManyField(User, blank=True, related_name='calendar_events')
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_calendar_events')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notification_sent = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.title} - {self.start_time.strftime('%d %b %Y %H:%M')}"
    
    class Meta:
        ordering = ['start_time']

# Task Management
class TaskCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=7, default='#3b82f6')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Task Categories"
        ordering = ['name']

class TaskStage(models.Model):
    name = models.CharField(max_length=100, unique=True)
    order = models.PositiveIntegerField(default=0)
    color = models.CharField(max_length=7, default='#6b7280')
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['order']

class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.ForeignKey(TaskCategory, on_delete=models.SET_NULL, null=True, blank=True)
    stage = models.ForeignKey(TaskStage, on_delete=models.CASCADE)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    due_date = models.DateField(null=True, blank=True)
    due_time = models.TimeField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Hierarchy support
    parent_task = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subtasks')
    order = models.PositiveIntegerField(default=0, help_text="Order within parent or stage")
    original_stage = models.ForeignKey(TaskStage, on_delete=models.SET_NULL, null=True, blank=True, related_name='original_tasks', help_text="Original stage for subtasks")
    
    # Event/Meeting details
    venue = models.CharField(max_length=255, blank=True, help_text="Meeting venue or event location")
    location = models.TextField(blank=True, help_text="Full address or location details")
    event_date = models.DateTimeField(null=True, blank=True, help_text="Event or meeting date/time")
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True, related_name='tasks')
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, null=True, blank=True, related_name='tasks')
    assigned_to = models.ManyToManyField(User, blank=True, related_name='assigned_tasks')
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    def mark_as_complete(self):
        self.completed = True
        self.completed_at = timezone.now()
        self.save()
        
        # Update parent task completion if all subtasks are complete
        if self.parent_task:
            parent = self.parent_task
            all_subtasks_complete = parent.subtasks.filter(completed=False).count() == 0
            if all_subtasks_complete and not parent.completed:
                parent.mark_as_complete()
    
    @property
    def is_overdue(self):
        if self.due_date and not self.completed:
            return self.due_date < timezone.now().date()
        return False
    
    @property
    def is_parent_task(self):
        return self.subtasks.exists()
    
    @property
    def completion_percentage(self):
        if not self.is_parent_task:
            return 100 if self.completed else 0
        
        subtasks = self.subtasks.all()
        if not subtasks:
            return 100 if self.completed else 0
        
        completed_subtasks = subtasks.filter(completed=True).count()
        return (completed_subtasks / subtasks.count()) * 100
    
    def get_hierarchy_level(self):
        level = 0
        current = self.parent_task
        while current:
            level += 1
            current = current.parent_task
        return level
    
    def save(self, *args, **kwargs):
        # Set original stage for subtasks
        if self.parent_task and not self.original_stage:
            self.original_stage = self.parent_task.stage
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['order', '-created_at']

# Notification System
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('lead', 'Lead'),
        ('task', 'Task'),
        ('event', 'Event'),
        ('birthday', 'Birthday'),
        ('anniversary', 'Anniversary'),
        ('system', 'System'),
        ('announcement', 'Announcement'),
        ('ivr_call', 'IVR Call'),
        ('whatsapp', 'WhatsApp'),
        ('stage_change', 'Stage Change'),
    ]
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='system')
    is_read = models.BooleanField(default=False)
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object_type = models.CharField(max_length=50, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.recipient.get_full_name()}"
    
    class Meta:
        ordering = ['-created_at']

# Leave Management
class LeaveType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    days_allowed_per_year = models.PositiveIntegerField(default=0)
    carry_forward_allowed = models.BooleanField(default=False)
    max_carry_forward_days = models.PositiveIntegerField(default=0)
    requires_approval = models.BooleanField(default=True)
    color = models.CharField(max_length=7, default='#f59e0b')
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

class LeaveApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_applications')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    from_date = models.DateField()
    to_date = models.DateField()
    days_requested = models.PositiveIntegerField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.days_requested:
            self.days_requested = (self.to_date - self.from_date).days + 1
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.leave_type.name} ({self.from_date} to {self.to_date})"
    
    class Meta:
        ordering = ['-created_at']

class CompOffRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='compoff_requests')
    worked_date = models.DateField(help_text="Date when extra work was done")
    requested_date = models.DateField(help_text="Date when comp-off is requested")
    reason = models.TextField(help_text="Reason for working on holiday/weekend")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_compoffs')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - Comp-off for {self.worked_date}"
    
    class Meta:
        ordering = ['-created_at']

# Attendance Management
class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('half_day', 'Half Day'),
        ('work_from_home', 'Work From Home'),
        ('on_leave', 'On Leave'),
        ('comp_off', 'Comp Off'),
    ]
    
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present')
    notes = models.TextField(blank=True)
    
    working_hours = models.FloatField(null=True, blank=True)
    
    # Location tracking
    check_in_latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    check_in_longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    check_in_address = models.TextField(blank=True)
    check_out_latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    check_out_longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    check_out_address = models.TextField(blank=True)
    
    # Leave/CompOff references
    leave_application = models.ForeignKey(LeaveApplication, on_delete=models.SET_NULL, null=True, blank=True)
    compoff_request = models.ForeignKey(CompOffRequest, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_attendance')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_manual_entry = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.date} - {self.get_status_display()}"
    
    def calculate_status(self):
        if not self.check_in_time:
            return 'absent'
        
        office_start = time(9, 30)
        late_threshold = time(10, 30)
        half_day_threshold = time(12, 0)
        
        if self.check_in_time <= office_start:
            return 'present'
        elif self.check_in_time <= late_threshold:
            return 'late'
        elif self.check_in_time <= half_day_threshold:
            return 'half_day'
        else:
            return 'half_day'
    
    def save(self, *args, **kwargs):
        if self.check_in_time and self.check_out_time:
            from datetime import datetime, timedelta
            check_in = datetime.combine(self.date, self.check_in_time)
            check_out = datetime.combine(self.date, self.check_out_time)
            
            if check_out < check_in:
                check_out += timedelta(days=1)
            
            duration = check_out - check_in
            self.working_hours = duration.total_seconds() / 3600
        
        super().save(*args, **kwargs)
    
    class Meta:
        unique_together = ['employee', 'date']
        ordering = ['-date', 'employee__first_name']
