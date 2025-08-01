from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # AJAX endpoints
    path('ajax/search-projects/', views.search_projects, name='search_projects'),
    path('ajax/create-brochure-lead/', views.create_brochure_lead, name='create_brochure_lead'),
    path('ajax/assign-lead/', views.assign_lead, name='assign_lead'),
    path('ajax/update-lead-status/', views.update_lead_status, name='update_lead_status'),
    
    # Projects
    path('projects/', views.projects, name='projects'),
    path('projects/add/', views.add_project, name='add_project'),
    path('projects/<int:project_id>/', views.project_details, name='project_details'),
    path('projects/<int:project_id>/edit/', views.edit_project, name='edit_project'),
    path('projects/<int:project_id>/delete/', views.delete_project, name='delete_project'),
    path('projects/image/<int:image_id>/delete/', views.delete_project_image, name='delete_project_image'),
    path('projects/<int:project_id>/units/', views.manage_project_units, name='manage_project_units'),
    path('projects/units/add/<int:project_id>/', views.add_project_unit, name='add_project_unit'),
    path('projects/units/<int:unit_id>/edit/', views.edit_project_unit, name='edit_project_unit'),
    path('projects/units/<int:unit_id>/delete/', views.delete_project_unit, name='delete_project_unit'),

    # Leads
    path('leads/', views.leads, name='leads'),
    path('leads/active/', views.active_leads, name='active_leads'),
    path('leads/hot/', views.hot_leads, name='hot_leads'),
    path('leads/followup/', views.followup_leads, name='followup_leads'),
    path('leads/closed/', views.closed_leads, name='closed_leads'),
    path('leads/add/', views.add_lead, name='add_lead'),
    path('leads/<int:lead_id>/', views.view_lead, name='view_lead'),
    path('leads/<int:lead_id>/edit/', views.edit_lead, name='edit_lead'),
    path('leads/bulk-upload/', views.bulk_upload_leads, name='bulk_upload_leads'),
    
    # Lead Notes
    path('ajax/add-lead-note/', views.add_lead_note, name='add_lead_note'),
    path('ajax/check-duplicate-leads/', views.check_duplicate_leads, name='check_duplicate_leads'),
    path('ajax/mark-duplicate-lead/', views.mark_duplicate_lead, name='mark_duplicate_lead'),
    path('ajax/merge-duplicate-lead/', views.merge_duplicate_lead, name='merge_duplicate_lead'),
    
    # Team
    path('team/', views.team, name='team'),
    path('team/hierarchy/', views.team_hierarchy, name='team_hierarchy'),
    path('team/add/', views.add_member, name='add_member'),
    path('team/<int:member_id>/edit/', views.edit_member, name='edit_member'),
    path('team/<int:member_id>/delete/', views.delete_member, name='delete_member'),
    
    # Profile
    path('profile/', views.profile, name='profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    
    # Reports
    path('reports/', views.reports, name='reports'),
    
    # Other pages
    path('earnings/', views.earnings, name='earnings'),
    path('clients/', views.clients, name='clients'),
    path('clients/add/', views.add_client, name='add_client'),
    
    # Calendar
    path('calendar/', views.calendar, name='calendar'),
    path('calendar/events.json', views.calendar_events_json, name='calendar_events_json'),
    path('calendar/add-event/', views.add_event, name='add_event'),
    path('calendar/<int:event_id>/edit/', views.edit_event, name='edit_event'),
    path('calendar/<int:event_id>/delete/', views.delete_event, name='delete_event'),
    
    # Tasks
    path('tasks/', views.tasks, name='tasks'),
    path('tasks/categories/', views.task_categories, name='task_categories'),
    path('tasks/add/', views.add_task, name='add_task'),
    path('tasks/<int:task_id>/edit/', views.edit_task, name='edit_task'),
    path('tasks/<int:task_id>/detail/', views.task_detail, name='task_detail'),
    path('tasks/<int:task_id>/complete/', views.complete_task, name='complete_task'),
    path('tasks/<int:task_id>/delete/', views.delete_task, name='delete_task'),
    
    # Analytics
    path('analytics/', views.analytics, name='analytics'),

    # Automation URLs
    path('automation/', views.automation, name='automation'),
    path('automation/bulk-email/', views.bulk_email, name='bulk_email'),
    path('automation/bulk-whatsapp/', views.bulk_whatsapp, name='bulk_whatsapp'),
    path('automation/bulk-sms/', views.bulk_sms, name='bulk_sms'),
    
    # Notifications
    path('notifications/', views.notifications, name='notifications'),
    path('ajax/notifications/', views.get_notifications_json, name='get_notifications_json'),
    path('ajax/notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('ajax/notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('ajax/notifications/<int:notification_id>/acknowledge/', views.acknowledge_notification, name='acknowledge_notification'),
    
    # Attendance
    path('attendance/', views.attendance, name='attendance'),
    path('punch-attendance/', views.punch_attendance, name='punch_attendance'),
    path('ajax/punch-in-out/', views.punch_in_out, name='punch_in_out'),
    path('ajax/add-attendance/', views.add_attendance, name='add_attendance'),
    
    # TATA IVR Calls
    path('tata-calls/', views.tata_calls, name='tata_calls'),
    path('ajax/sync-tata-calls/', views.sync_tata_calls, name='sync_tata_calls'),
    
    # TATA Chat Panel
    path('tata-chat/', views.tata_chat_panel, name='tata_chat_panel'),
    path('ajax/tata-conversations/', views.get_tata_conversations, name='get_tata_conversations'),
    path('ajax/tata-send-reply/', views.send_tata_reply, name='send_tata_reply'),
    path('webhook/', views.tata_webhook, name='tata_webhook'),
    path('ivr-webhooks/', views.ivr_webhooks, name='ivr_webhooks'),
]
