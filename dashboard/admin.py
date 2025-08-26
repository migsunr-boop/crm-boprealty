from django.contrib import admin
from .models import (
    Project, ProjectImage, Lead, LeadNote, LeadStage, LeadStageHistory,
    TeamMember, Meeting, Earning, Task, TaskStage, TaskCategory, 
    CalendarEvent, Notification, Attendance, IVRCallLog,
    WhatsAppTemplate, WhatsAppMessage, Event, EventRegistration,
    LeadSource, MarketingExpense, ProjectUnit, Client,
    LeaveType, LeaveApplication, CompOffRequest
)

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'status', 'price_min', 'price_max', 'total_units', 'available_units', 'created_at']
    list_filter = ['status', 'property_type', 'created_at', 'possession_date', 'is_featured']
    search_fields = ['name', 'location', 'developer_name', 'city']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = []
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'location', 'city', 'state', 'pincode', 'description', 'property_type', 'bhk_options', 'status')
        }),
        ('Pricing & Units', {
            'fields': ('price_min', 'price_max', 'area_min', 'area_max', 'total_units', 'available_units', 'possession_date')
        }),
        ('Contact & IVR', {
            'fields': ('developer_name', 'contact_person', 'contact_phone', 'contact_email', 'ivr_number')
        }),
        ('Media & Virtual Tour', {
            'fields': ('main_image', 'floor_plan', 'virtual_tour_url', 'video_url', 'brochure_pdf')
        }),
        ('Features & Amenities', {
            'fields': ('amenities', 'features', 'nearby_schools', 'nearby_hospitals', 'nearby_malls', 'transportation')
        }),
        ('Legal & RERA', {
            'fields': ('rera_number', 'approval_status')
        }),
        ('Meta', {
            'fields': ('created_by', 'is_active', 'is_featured', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(ProjectUnit)
class ProjectUnitAdmin(admin.ModelAdmin):
    list_display = ('project', 'unit_number', 'floor', 'size', 'price', 'status')
    list_filter = ('project', 'status', 'floor')
    search_fields = ('project__name', 'unit_number')

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'source', 'created_by', 'created_at')
    list_filter = ('source', 'created_at')
    search_fields = ('name', 'phone')

@admin.register(ProjectImage)
class ProjectImageAdmin(admin.ModelAdmin):
    list_display = ['project', 'caption', 'is_featured', 'uploaded_at']
    list_filter = ['is_featured', 'uploaded_at']
    search_fields = ['project__name', 'caption']
    readonly_fields = ['uploaded_at']

@admin.register(LeadStage)
class LeadStageAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'order', 'color', 'is_active', 'auto_progress_days']
    list_filter = ['category', 'is_active', 'requires_action', 'is_final_stage']
    search_fields = ['name', 'description']
    list_editable = ['order', 'is_active']
    ordering = ['category', 'order']

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'current_stage', 'source', 'assigned_to', 'is_recapture', 'created_at']
    list_filter = ['current_stage', 'source', 'is_recapture', 'industry', 'created_at', 'assigned_to']
    search_fields = ['name', 'email', 'phone', 'alternative_phone']
    filter_horizontal = ['interested_projects']
    readonly_fields = ['created_at', 'updated_at', 'stage_changed_at', 'recapture_count']
    raw_id_fields = ['assigned_to', 'sticky_agent', 'current_stage', 'previous_stage', 'original_lead']
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'phone', 'alternative_phone', 'alternative_email', 'alternative_contact_person')
        }),
        ('Lead Details', {
            'fields': ('source', 'source_details', 'current_stage', 'previous_stage', 'quality_score', 'notes')
        }),
        ('Buyer Persona', {
            'fields': ('budget_min', 'budget_max', 'preferred_location', 'city', 'state', 'industry', 'job_function', 'company_name', 'annual_income')
        }),
        ('Goals & Pain Points', {
            'fields': ('pain_points', 'goals_objectives', 'timeline')
        }),
        ('UTM Tracking', {
            'fields': ('utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term'),
            'classes': ('collapse',)
        }),
        ('Technical Tracking', {
            'fields': ('ip_address', 'user_agent', 'referrer_url', 'landing_page'),
            'classes': ('collapse',)
        }),
        ('Follow-up Information', {
            'fields': ('follow_up_date', 'last_contact_date', 'next_action', 'requires_callback', 'callback_time')
        }),
        ('Assignment & Recapture', {
            'fields': ('assigned_to', 'sticky_agent', 'interested_projects', 'is_recapture', 'recapture_count', 'is_duplicate', 'original_lead')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'stage_changed_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(LeadStageHistory)
class LeadStageHistoryAdmin(admin.ModelAdmin):
    list_display = ['lead', 'from_stage', 'to_stage', 'changed_by', 'changed_at', 'duration_in_previous_stage']
    list_filter = ['from_stage', 'to_stage', 'changed_at', 'changed_by']
    search_fields = ['lead__name', 'notes']
    readonly_fields = ['changed_at', 'duration_in_previous_stage']
    raw_id_fields = ['lead', 'from_stage', 'to_stage', 'changed_by']

@admin.register(LeadNote)
class LeadNoteAdmin(admin.ModelAdmin):
    list_display = ['lead', 'call_type', 'call_outcome', 'created_by', 'created_at']
    list_filter = ['call_type', 'call_outcome', 'created_at', 'created_by']
    search_fields = ['lead__name', 'note', 'next_action']
    readonly_fields = ['created_at']
    raw_id_fields = ['lead']
    filter_horizontal = ['meeting_attendees']
    
    fieldsets = (
        ('Note Details', {
            'fields': ('lead', 'call_type', 'call_outcome', 'note', 'next_action', 'follow_up_date')
        }),
        ('Call Details', {
            'fields': ('call_duration', 'call_recording_url')
        }),
        ('Meeting Details', {
            'fields': ('meeting_location', 'meeting_attendees')
        }),
        ('Meta', {
            'fields': ('created_by', 'created_at')
        }),
    )

@admin.register(WhatsAppTemplate)
class WhatsAppTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'stage', 'is_active', 'created_at']
    list_filter = ['stage', 'is_active', 'created_at']
    search_fields = ['name', 'message_template']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(WhatsAppMessage)
class WhatsAppMessageAdmin(admin.ModelAdmin):
    list_display = ['lead', 'template', 'phone_number', 'status', 'sent_at']
    list_filter = ['status', 'sent_at', 'template']
    search_fields = ['lead__name', 'phone_number', 'message_content']
    readonly_fields = ['created_at', 'sent_at', 'delivered_at', 'read_at', 'failed_at']
    raw_id_fields = ['lead', 'template']

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['name', 'event_type', 'start_date', 'location', 'registration_count', 'is_active']
    list_filter = ['event_type', 'is_active', 'is_published', 'start_date']
    search_fields = ['name', 'description', 'location']
    filter_horizontal = ['featured_projects', 'team_members']
    readonly_fields = ['created_at', 'updated_at', 'registration_count']
    
    fieldsets = (
        ('Event Details', {
            'fields': ('name', 'event_type', 'description')
        }),
        ('Date & Location', {
            'fields': ('start_date', 'end_date', 'location', 'venue_address')
        }),
        ('Registration', {
            'fields': ('registration_required', 'max_capacity', 'registration_deadline')
        }),
        ('Projects & Team', {
            'fields': ('featured_projects', 'team_members')
        }),
        ('Status', {
            'fields': ('is_active', 'is_published')
        }),
        ('Meta', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ['event', 'lead', 'registered_at', 'attended', 'follow_up_completed']
    list_filter = ['attended', 'follow_up_required', 'follow_up_completed', 'registered_at']
    search_fields = ['event__name', 'lead__name']
    readonly_fields = ['registered_at', 'attended_at']
    raw_id_fields = ['event', 'lead']

@admin.register(LeadSource)
class LeadSourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'monthly_leads', 'cost_per_lead', 'conversion_rate', 'is_active']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'category']
    readonly_fields = ['created_at', 'monthly_leads', 'conversion_rate']

@admin.register(MarketingExpense)
class MarketingExpenseAdmin(admin.ModelAdmin):
    list_display = ['campaign_name', 'category', 'amount', 'date', 'leads_generated', 'cost_per_lead']
    list_filter = ['category', 'date', 'created_by']
    search_fields = ['campaign_name', 'vendor', 'invoice_number']
    readonly_fields = ['created_at', 'cost_per_lead']
    
    fieldsets = (
        ('Campaign Details', {
            'fields': ('category', 'campaign_name', 'amount', 'date')
        }),
        ('Vendor Information', {
            'fields': ('vendor', 'invoice_number', 'description')
        }),
        ('Performance', {
            'fields': ('leads_generated', 'cost_per_lead')
        }),
        ('Meta', {
            'fields': ('created_by', 'created_at')
        }),
    )

@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone', 'date_of_birth', 'joining_date', 'manager']
    list_filter = ['role', 'joining_date', 'manager']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'phone']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'role', 'phone', 'date_of_birth', 'joining_date', 'profile_picture')
        }),
        ('Performance Targets', {
            'fields': ('target_leads_monthly', 'target_site_visits_monthly', 'target_closures_monthly')
        }),
        ('Hierarchy', {
            'fields': ('manager',)
        }),
        ('Permissions', {
            'fields': (
                'can_access_dashboard', 'can_access_projects', 'can_access_leads',
                'can_access_reports', 'can_access_earnings', 'can_access_clients',
                'can_access_calendar', 'can_access_tasks', 'can_access_analytics'
            )
        }),
    )

@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ['lead', 'project', 'meeting_date', 'location', 'created_by']
    list_filter = ['meeting_date', 'created_by', 'project']
    search_fields = ['lead__name', 'project__name', 'location']
    filter_horizontal = ['attendees']
    readonly_fields = ['created_at']

@admin.register(Earning)
class EarningAdmin(admin.ModelAdmin):
    list_display = ['project', 'lead', 'commission_amount', 'date_earned', 'earned_by']
    list_filter = ['date_earned', 'earned_by', 'project']
    search_fields = ['project__name', 'lead__name']
    readonly_fields = ['created_at']

@admin.register(TaskCategory)
class TaskCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'description', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']

@admin.register(TaskStage)
class TaskStageAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'color']
    list_editable = ['order']
    ordering = ['order']

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'parent_task', 'stage', 'priority', 'due_date', 'completed', 'created_by', 'order']
    list_filter = ['stage', 'priority', 'completed', 'due_date', 'category', 'parent_task']
    search_fields = ['title', 'description']
    filter_horizontal = ['assigned_to']
    readonly_fields = ['created_at', 'updated_at', 'completed_at', 'is_parent_task', 'completion_percentage', 'get_hierarchy_level']
    
    fieldsets = (
        ('Task Details', {
            'fields': ('title', 'description', 'stage', 'priority', 'category')
        }),
        ('Hierarchy', {
            'fields': ('parent_task', 'order', 'is_parent_task', 'completion_percentage', 'get_hierarchy_level')
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'created_by')
        }),
        ('Related Items', {
            'fields': ('project', 'lead')
        }),
        ('Dates & Location', {
            'fields': ('due_date', 'due_time', 'event_date', 'venue', 'location')
        }),
        ('Status', {
            'fields': ('completed', 'completed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_parent_task(self, obj):
        return obj.is_parent_task
    is_parent_task.boolean = True
    is_parent_task.short_description = "Has Subtasks"
    
    def completion_percentage(self, obj):
        return f"{obj.completion_percentage:.1f}%"
    completion_percentage.short_description = "Completion %"
    
    def get_hierarchy_level(self, obj):
        return obj.get_hierarchy_level()
    get_hierarchy_level.short_description = "Hierarchy Level"

@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ['title', 'event_type', 'start_time', 'end_time', 'created_by']
    list_filter = ['event_type', 'all_day', 'start_time', 'created_by']
    search_fields = ['title', 'description', 'location']
    filter_horizontal = ['attendees']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Event Details', {
            'fields': ('title', 'description', 'event_type', 'color')
        }),
        ('Time & Location', {
            'fields': ('start_time', 'end_time', 'all_day', 'location')
        }),
        ('People', {
            'fields': ('created_by', 'attendees')
        }),
        ('Related Items', {
            'fields': ('project', 'lead')
        }),
        ('Notifications', {
            'fields': ('notification_sent',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'recipient', 'notification_type', 'is_read', 'is_acknowledged', 'created_at']
    list_filter = ['notification_type', 'is_read', 'is_acknowledged', 'created_at']
    search_fields = ['title', 'message', 'recipient__username']
    readonly_fields = ['created_at', 'acknowledged_at']
    
    fieldsets = (
        ('Notification Details', {
            'fields': ('recipient', 'title', 'message', 'notification_type')
        }),
        ('Status', {
            'fields': ('is_read', 'is_acknowledged', 'acknowledged_at')
        }),
        ('Related Object', {
            'fields': ('related_object_type', 'related_object_id')
        }),
        ('Meta', {
            'fields': ('created_at',)
        }),
    )

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'status', 'check_in_time', 'check_out_time', 'get_working_hours']
    list_filter = ['status', 'date', 'employee', 'leave_application', 'compoff_request']
    search_fields = ['employee__username', 'employee__first_name', 'employee__last_name']
    readonly_fields = ['created_at', 'updated_at', 'get_working_hours']
    raw_id_fields = ['leave_application', 'compoff_request']
    
    fieldsets = (
        ('Employee & Date', {
            'fields': ('employee', 'date', 'status')
        }),
        ('Time Tracking', {
            'fields': ('check_in_time', 'check_out_time', 'get_working_hours')
        }),
        ('Leave/CompOff References', {
            'fields': ('leave_application', 'compoff_request')
        }),
        ('Location Tracking', {
            'fields': ('check_in_latitude', 'check_in_longitude', 'check_in_address', 'check_out_latitude', 'check_out_longitude', 'check_out_address'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Meta', {
            'fields': ('created_by', 'is_manual_entry', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_working_hours(self, obj):
        """Display working hours in admin"""
        hours = obj.working_hours
        if hours:
            return f"{hours:.2f} hours"
        return "N/A"
    get_working_hours.short_description = "Working Hours"

@admin.register(IVRCallLog)
class IVRCallLogAdmin(admin.ModelAdmin):
    list_display = ['uuid', 'caller_id_number', 'call_to_number', 'status', 'duration_display', 'start_stamp', 'associated_lead', 'processed']
    list_filter = ['status', 'processed', 'start_stamp']
    search_fields = ['uuid', 'caller_id_number', 'call_to_number', 'customer_no_with_prefix']
    readonly_fields = ['created_at', 'call_duration_formatted', 'raw_data']
    raw_id_fields = ['associated_lead']
    
    fieldsets = (
        ('Call Information', {
            'fields': ('uuid', 'caller_id_number', 'call_to_number', 'call_id', 'status')
        }),
        ('Timing', {
            'fields': ('start_stamp', 'end_stamp', 'duration', 'call_duration_formatted')
        }),
        ('IVR Data', {
            'fields': ('billing_circle', 'customer_no_with_prefix')
        }),
        ('Associations', {
            'fields': ('associated_lead',)
        }),
        ('Processing', {
            'fields': ('processed',)
        }),
        ('Raw IVR Data', {
            'fields': ('raw_data',),
            'classes': ('collapse',),
            'description': 'Complete data received from IVR system'
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def duration_display(self, obj):
        return obj.call_duration_formatted
    duration_display.short_description = "Duration"
    
    actions = ['mark_as_processed', 'associate_with_leads', 'create_leads_from_calls']
    
    def mark_as_processed(self, request, queryset):
        updated = queryset.update(processed=True)
        self.message_user(request, f'{updated} call logs marked as processed.')
    mark_as_processed.short_description = "Mark selected calls as processed"
    
    def associate_with_leads(self, request, queryset):
        count = 0
        for call_log in queryset:
            if not call_log.associated_lead:
                if call_log.associate_with_lead():
                    count += 1
        self.message_user(request, f'{count} call logs associated with existing leads.')
    associate_with_leads.short_description = "Associate selected calls with existing leads"
    
    def create_leads_from_calls(self, request, queryset):
        count = 0
        for call_log in queryset:
            if not call_log.associated_lead:
                lead = call_log.create_lead_from_call()
                if lead:
                    count += 1
        self.message_user(request, f'{count} new leads created from call logs.')
    create_leads_from_calls.short_description = "Create new leads from unassociated calls"

@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'days_allowed_per_year', 'carry_forward_allowed', 'max_carry_forward_days', 'requires_approval']
    list_filter = ['carry_forward_allowed', 'requires_approval']
    search_fields = ['name']
    
@admin.register(LeaveApplication)
class LeaveApplicationAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_type', 'from_date', 'to_date', 'days_requested', 'status', 'created_at']
    list_filter = ['leave_type', 'status', 'from_date', 'approved_by']
    search_fields = ['employee__username', 'employee__first_name', 'employee__last_name', 'reason']
    readonly_fields = ['created_at', 'updated_at', 'approved_at']
    raw_id_fields = ['employee', 'approved_by']
    
    fieldsets = (
        ('Leave Details', {
            'fields': ('employee', 'leave_type', 'from_date', 'to_date', 'days_requested', 'reason')
        }),
        ('Status', {
            'fields': ('status', 'approved_by', 'approved_at', 'rejection_reason')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
@admin.register(CompOffRequest)
class CompOffRequestAdmin(admin.ModelAdmin):
    list_display = ['employee', 'worked_date', 'requested_date', 'status', 'created_at']
    list_filter = ['status', 'worked_date', 'approved_by']
    search_fields = ['employee__username', 'employee__first_name', 'employee__last_name', 'reason']
    readonly_fields = ['created_at', 'updated_at', 'approved_at']
    raw_id_fields = ['employee', 'approved_by']
    
    fieldsets = (
        ('Comp-Off Details', {
            'fields': ('employee', 'worked_date', 'requested_date', 'reason')
        }),
        ('Status', {
            'fields': ('status', 'approved_by', 'approved_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )