from django.urls import path
from . import views
from . import tata_campaign_views
from . import tata_webhook_handler
from . import whatsapp_webhook_handler
from . import ivr_webhook_handler
from . import whatsapp_tracking_views
from . import ivr_leads_views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # TATA Integration
    path('tata-chat/', views.tata_chat_panel, name='tata_chat_panel'),
    path('tata-sync/', views.tata_sync_panel, name='tata_sync_panel'),
    path('ajax/tata-conversations/', views.get_tata_conversations, name='get_tata_conversations'),
    path('ajax/tata-send-reply/', views.send_tata_reply, name='send_tata_reply'),
    path('webhook/', views.tata_webhook, name='tata_webhook'),
    
    # WhatsApp Campaigns (Production)
    path('whatsapp-campaigns/', tata_campaign_views.whatsapp_campaign_dashboard, name='whatsapp_campaigns'),
    path('whatsapp-campaigns/run/', tata_campaign_views.run_whatsapp_campaign, name='run_whatsapp_campaign'),
    path('whatsapp-campaigns/preview/', tata_campaign_views.campaign_preview, name='campaign_preview'),
    path('whatsapp-campaigns/status/', tata_campaign_views.campaign_status, name='campaign_status'),
    path('whatsapp-campaigns/analytics/', tata_campaign_views.campaign_analytics, name='campaign_analytics'),
    
    # Template and Media Validation
    path('api/validate-template/', tata_campaign_views.template_validator, name='template_validator'),
    path('api/validate-media/', tata_campaign_views.media_validator, name='media_validator'),
    
    # WhatsApp Webhooks (Production)
    path('webhook/whatsapp/', tata_webhook_handler.whatsapp_webhook, name='whatsapp_webhook'),
    path('webhook/whatsapp/delivery/', tata_webhook_handler.whatsapp_delivery_webhook, name='whatsapp_delivery_webhook'),
    path('webhook/whatsapp/messages/', tata_webhook_handler.whatsapp_message_webhook, name='whatsapp_message_webhook'),
    
    # IVR WhatsApp Integration Webhooks
    path('webhook/whatsapp/integration/', whatsapp_webhook_handler.whatsapp_webhook_handler, name='whatsapp_integration_webhook'),
    path('webhook/whatsapp/integration/delivery/', whatsapp_webhook_handler.whatsapp_delivery_webhook, name='whatsapp_integration_delivery'),
    path('webhook/whatsapp/integration/messages/', whatsapp_webhook_handler.whatsapp_message_webhook, name='whatsapp_integration_messages'),
    
    # WhatsApp Interactive Features
    path('whatsapp-interactive/', whatsapp_tracking_views.whatsapp_interactive, name='whatsapp_interactive'),
    path('track/<int:lead_id>/', whatsapp_tracking_views.track_response, name='track_response'),
    path('send-interactive-message/', whatsapp_tracking_views.send_interactive_message, name='send_interactive_message'),
    path('generate-ai-template/', whatsapp_tracking_views.generate_ai_template, name='generate_ai_template'),
    path('interactive-analytics/', whatsapp_tracking_views.interactive_analytics, name='interactive_analytics'),
    
    # IVR Leads Management
    path('ivr-leads/', ivr_leads_views.ivr_leads_dashboard, name='ivr_leads'),
    path('send-whatsapp-ivr-leads/', ivr_leads_views.send_whatsapp_to_ivr_leads, name='send_whatsapp_ivr_leads'),
    path('ivr-lead-analytics/', ivr_leads_views.ivr_lead_analytics, name='ivr_lead_analytics'),
    path('sync-ivr-data/', ivr_leads_views.sync_ivr_data, name='sync_ivr_data'),
    
    # TATA Sync API endpoints
    path('api/sync-tata-templates/', views.sync_tata_templates, name='sync_tata_templates'),
    path('api/sync-tata-messages/', views.sync_tata_messages, name='sync_tata_messages'),
    path('api/sync-all-tata-data/', views.sync_all_tata_data, name='sync_all_tata_data'),
    path('api/get-tata-templates/', views.get_tata_templates, name='get_tata_templates'),
    path('api/get-all-messages/', views.get_all_messages, name='get_all_messages'),
    
    # Projects
    path('projects/', views.projects, name='projects'),
    path('projects/add/', views.add_project, name='add_project'),
    path('projects/<int:project_id>/', views.project_details, name='project_details'),
    path('projects/<int:project_id>/edit/', views.edit_project, name='edit_project'),
    path('projects/<int:project_id>/delete/', views.delete_project, name='delete_project'),
    path('projects/<int:project_id>/units/', views.manage_project_units, name='manage_project_units'),
    path('projects/<int:project_id>/units/add/', views.add_project_unit, name='add_project_unit'),
    path('projects/units/<int:unit_id>/edit/', views.edit_project_unit, name='edit_project_unit'),
    path('projects/units/<int:unit_id>/delete/', views.delete_project_unit, name='delete_project_unit'),
    path('ajax/delete-project-image/<int:image_id>/', views.delete_project_image, name='delete_project_image'),
    
    # Leads
    path('leads/', views.leads, name='leads'),
    path('leads/add/', views.add_lead, name='add_lead'),
    path('leads/<int:lead_id>/edit/', views.edit_lead, name='edit_lead'),
    path('leads/<int:lead_id>/view/', views.view_lead, name='view_lead'),
    path('leads/active/', views.active_leads, name='active_leads'),
    path('leads/hot/', views.hot_leads, name='hot_leads'),
    path('leads/followup/', views.followup_leads, name='followup_leads'),
    path('leads/closed/', views.closed_leads, name='closed_leads'),
    path('leads/bulk-upload/', views.bulk_upload_leads, name='bulk_upload_leads'),
    path('ajax/create-brochure-lead/', views.create_brochure_lead, name='create_brochure_lead'),
    
    # Lead Management
    path('lead-stages/', views.lead_stage_management, name='lead_stage_management'),
    path('leads/<int:lead_id>/journey/', views.lead_journey_tracking, name='lead_journey_tracking'),
    path('ajax/move-lead-stage/', views.move_lead_stage, name='move_lead_stage'),
    path('ajax/check-duplicate-leads/', views.check_duplicate_leads, name='check_duplicate_leads'),
    path('ajax/mark-duplicate-lead/', views.mark_duplicate_lead, name='mark_duplicate_lead'),
    path('ajax/merge-duplicate-lead/', views.merge_duplicate_lead, name='merge_duplicate_lead'),
    
    # Team
    path('team/', views.team, name='team'),
    path('team/add/', views.add_member, name='add_member'),
    path('team/<int:member_id>/edit/', views.edit_member, name='edit_member'),
    path('team/<int:member_id>/delete/', views.delete_member, name='delete_member'),
    path('team/hierarchy/', views.team_hierarchy, name='team_hierarchy'),
    
    # Calendar
    path('calendar/', views.calendar, name='calendar'),
    path('calendar/events.json', views.calendar_events_json, name='calendar_events_json'),
    path('calendar/add-event/', views.add_event, name='add_event'),
    path('calendar/<int:event_id>/edit/', views.edit_event, name='edit_event'),
    path('calendar/<int:event_id>/delete/', views.delete_event, name='delete_event'),
    
    # Tasks
    path('tasks/', views.tasks, name='tasks'),
    path('tasks/enhanced/', views.tasks_enhanced, name='tasks_enhanced'),
    path('tasks/add/', views.add_task, name='add_task'),
    path('tasks/<int:task_id>/edit/', views.edit_task, name='edit_task'),
    path('tasks/<int:task_id>/detail/', views.task_detail, name='task_detail'),
    path('tasks/<int:task_id>/complete/', views.complete_task, name='complete_task'),
    path('tasks/<int:task_id>/delete/', views.delete_task, name='delete_task'),
    path('tasks/categories/', views.task_categories, name='task_categories'),
    path('ajax/move-task/', views.move_task, name='move_task'),
    path('ajax/update-task-assignees/', views.update_task_assignees, name='update_task_assignees'),
    path('ajax/add-subtask/', views.add_subtask, name='add_subtask'),
    path('tasks/<int:subtask_id>/toggle-complete/', views.toggle_subtask_complete, name='toggle_subtask_complete'),
    path('ajax/get-subtask-connections/', views.get_subtask_connections, name='get_subtask_connections'),
    path('ajax/update-task-field/', views.update_task_field, name='update_task_field'),
    
    # Profile API endpoints
    path('api/attendance-data/<int:year>/<int:month>/', views.api_attendance_data, name='api_attendance_data'),
    path('api/attendance/<str:date>/', views.api_attendance_today, name='api_attendance_today'),
    path('api/holidays-events/', views.api_holidays_events, name='api_holidays_events'),
    path('api/payslip-requests/', views.api_payslip_requests, name='api_payslip_requests'),
    path('api/leave-applications/', views.api_leave_applications, name='api_leave_applications'),
    
    # Reports & Analytics
    path('reports/', views.reports, name='reports'),
    path('analytics/', views.analytics, name='analytics'),
    path('analytics/advanced/', views.analytics_dashboard, name='analytics_dashboard'),
    path('earnings/', views.earnings, name='earnings'),
    
    # Clients
    path('clients/', views.clients, name='clients'),
    path('clients/add/', views.add_client, name='add_client'),
    
    # Automation & Bulk Operations
    path('automation/', views.automation, name='automation'),
    path('bulk-email/', views.bulk_email, name='bulk_email'),
    path('bulk-whatsapp/', views.bulk_whatsapp, name='bulk_whatsapp'),
    path('bulk-sms/', views.bulk_sms, name='bulk_sms'),
    path('whatsapp-automation/', views.whatsapp_automation, name='whatsapp_automation'),
    
    # Attendance
    path('punch-attendance/', views.punch_attendance, name='punch_attendance'),
    path('ajax/punch-in-out/', views.punch_in_out, name='punch_in_out'),
    path('attendance/', views.attendance, name='attendance'),
    path('attendance/add/', views.add_attendance, name='add_attendance'),
    
    # TATA Calls
    path('tata-calls/', views.tata_calls, name='tata_calls'),
    path('ajax/sync-tata-calls/', views.sync_tata_calls, name='sync_tata_calls'),
    path('ivr-webhooks/', views.ivr_webhooks, name='ivr_webhooks'),
    
    # TATA API endpoints
    path('api/tata/calls/', views.fetch_tata_calls, name='fetch_tata_calls'),
    path('api/tata/active-calls/', views.fetch_active_calls, name='fetch_active_calls'),
    path('api/tata/analytics/', views.fetch_call_analytics, name='fetch_call_analytics'),
    path('api/tata/schedule-call/', views.schedule_tata_call, name='schedule_tata_call'),
    path('api/tata/recording-status/<str:batch_id>/', views.get_recording_status, name='get_recording_status'),
    path('api/tata/export-calls/', views.export_call_data, name='export_call_data'),
    path('api/tata/dashboard/', views.tata_call_dashboard, name='tata_call_dashboard'),
    
    # IVR Webhook endpoints (matching your TATA configuration)
    path('webhook/ivr/calls/', ivr_webhook_handler.ivr_webhook_handler, name='ivr_calls_webhook'),
    path('ivr-webhooks/webhook/tata-tele/1/', views.handle_ivr_webhook, name='ivr_webhook_1'),
    path('ivr-webhooks/webhook/tata-tele/2/', views.handle_ivr_webhook, name='ivr_webhook_2'),
    
    # Property Search
    path('property-search/', views.property_search, name='property_search'),
    
    # Profile
    path('profile/', views.profile, name='profile'),
    path('change-password/', views.change_password, name='change_password'),
    
    # AJAX endpoints
    path('ajax/assign-lead/', views.assign_lead, name='assign_lead'),
    path('ajax/update-lead-status/', views.update_lead_status, name='update_lead_status'),
    path('ajax/add-lead-note/', views.add_lead_note, name='add_lead_note'),
    path('ajax/search-projects/', views.search_projects, name='search_projects'),
    
    # Notifications
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/json/', views.get_notifications_json, name='get_notifications_json'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/<int:notification_id>/acknowledge/', views.acknowledge_notification, name='acknowledge_notification'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('ajax/check-birthday-notifications/', views.check_birthday_notifications, name='check_birthday_notifications'),
    path('ajax/check-upcoming-events/', views.check_upcoming_events, name='check_upcoming_events'),
]