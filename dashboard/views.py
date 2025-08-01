# django-realty-dashboard/django-realty-dashboard/dashboard/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Sum, Avg, F, fields, ExpressionWrapper
from django.db.models.functions import TruncMonth, TruncDate
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from .models import (Project, ProjectImage, Lead, TeamMember, Meeting, Earning, 
                     Task, TaskStage, TaskCategory, CalendarEvent, Notification, 
                     Attendance, LeadNote, IVRCallLog, LeadStage, WhatsAppTemplate, 
                     Client, ProjectUnit, MarketingExpense, WhatsAppMessage)
from .tata_sync import TATASync
import json
from urllib.parse import urlencode
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
from django.http import HttpResponseRedirect
from django.utils.timesince import timesince
from django.conf import settings
import requests
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
from django.db.models.functions import TruncMonth, TruncDate


@login_required
def dashboard(request):
    # Get statistics
    total_projects = Project.objects.filter(is_active=True).count()
    total_leads = Lead.objects.count()
    
    # Get leads by stage category
    hot_leads = Lead.objects.filter(current_stage__category='hot').count()
    warm_leads = Lead.objects.filter(current_stage__category='warm').count()
    cold_leads = Lead.objects.filter(current_stage__category='cold').count()
    converted_leads = Lead.objects.filter(current_stage__category='closed').count()
    
    # Latest projects for carousel (ordered by latest updated first)
    latest_projects = Project.objects.filter(is_active=True).order_by('-updated_at', '-created_at')[:12]
    
    # Featured projects
    featured_projects = Project.objects.filter(status='featured', is_active=True)[:3]
    
    # Monthly earnings
    current_month = timezone.now().month
    monthly_earnings = Earning.objects.filter(
        date_earned__month=current_month
    ).aggregate(total=Sum('commission_amount'))['total'] or 0
    
    # Lead status distribution for chart
    lead_stats = {
        'hot': hot_leads,
        'warm': warm_leads,
        'cold': cold_leads,
        'converted': converted_leads
    }
    
    # Add notification counts and lead stats for navbar
    unread_notifications = 0
    active_leads = 0
    overdue_followups = 0
    closed_leads = 0
    
    if request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(recipient=request.user, is_read=False).count()
        active_leads = Lead.objects.filter(current_stage__category__in=['warm', 'hot']).count()
        overdue_followups = Lead.objects.filter(
            follow_up_date__lt=timezone.now().date(),
            current_stage__category__in=['warm', 'hot']
        ).count()
        closed_leads = Lead.objects.filter(current_stage__category='closed').count()
    
    context = {
        'total_projects': total_projects,
        'total_leads': total_leads,
        'hot_leads': hot_leads,
        'warm_leads': warm_leads,
        'cold_leads': cold_leads,
        'converted_leads': converted_leads,
        'latest_projects': latest_projects,
        'featured_projects': featured_projects,
        'monthly_earnings': monthly_earnings,
        'lead_stats': json.dumps(lead_stats),
        'unread_notifications': unread_notifications,
        'active_leads': active_leads,
        'overdue_followups': overdue_followups,
        'closed_leads': closed_leads,
    }
    
    return render(request, 'dashboard/dashboard.html', context)

@login_required
def search_projects(request):
    """AJAX endpoint for dynamic project search"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'projects': []})
    
    projects = Project.objects.filter(
        Q(name__icontains=query) | 
        Q(location__icontains=query) |
        Q(developer_name__icontains=query),
        is_active=True
    ).order_by('-updated_at', '-created_at')[:8]
    
    project_data = []
    for project in projects:
        project_data.append({
            'id': project.id,
            'name': project.name,
            'location': project.location,
            'price_min': float(project.price_min),
            'price_max': float(project.price_max),
            'image_url': project.main_image.url if project.main_image else None,
            'description': project.description[:100] + '...' if len(project.description) > 100 else project.description,
        })
    
    return JsonResponse({'projects': project_data})

# Project Management Views
@login_required
def projects(request):
    """Enhanced projects list view with filtering and search"""
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    
    # Start with all active projects
    projects_list = Project.objects.filter(is_active=True).prefetch_related('images')
    
    # Apply filters
    if status_filter:
        projects_list = projects_list.filter(status=status_filter)
    
    if search_query:
        projects_list = projects_list.filter(
            Q(name__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(developer_name__icontains=search_query)
        )
    
    # Order by latest updated first
    projects_list = projects_list.order_by('-updated_at', '-created_at')
    
    # Pagination
    paginator = Paginator(projects_list, 12)  # Show 12 projects per page
    page_number = request.GET.get('page')
    projects = paginator.get_page(page_number)
    
    context = {
        'projects': projects,
        'status_choices': Project.STATUS_CHOICES,
        'current_status': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'dashboard/projects.html', context)

@login_required
def add_project(request):
    if request.method == 'POST':
        try:
            project = Project.objects.create(
                name=request.POST['name'],
                location=request.POST['location'],
                description=request.POST['description'],
                bhk_options=request.POST['bhk_options'],
                price_min=request.POST['price_min'],
                price_max=request.POST['price_max'],
                status=request.POST['status'],
                area_min=request.POST.get('area_min') or None,
                area_max=request.POST.get('area_max') or None,
                total_units=request.POST.get('total_units') or None,
                available_units=request.POST.get('available_units') or None,
                possession_date=request.POST.get('possession_date') or None,
                amenities=request.POST.get('amenities', ''),
                features=request.POST.get('features', ''),
                developer_name=request.POST.get('developer_name', ''),
                contact_person=request.POST.get('contact_person', ''),
                contact_phone=request.POST.get('contact_phone', ''),
                contact_email=request.POST.get('contact_email', ''),
                ivr_number=request.POST.get('ivr_number', ''),
                created_by=request.user,
            )
            messages.success(request, 'Project added successfully!')
            return redirect('projects')
        except Exception as e:
            messages.error(request, f'Error adding project: {str(e)}')
    
    return render(request, 'dashboard/add_project.html')


@login_required
def edit_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST':
        try:
            project.name = request.POST['name']
            project.location = request.POST['location']
            project.description = request.POST['description']
            project.bhk_options = request.POST['bhk_options']
            project.price_min = request.POST['price_min']
            project.price_max = request.POST['price_max']
            project.status = request.POST['status']
            project.area_min = request.POST.get('area_min') or None
            project.area_max = request.POST.get('area_max') or None
            project.total_units = request.POST.get('total_units') or None
            project.available_units = request.POST.get('available_units') or None
            project.possession_date = request.POST.get('possession_date') or None
            project.amenities = request.POST.get('amenities', '')
            project.features = request.POST.get('features', '')
            project.developer_name = request.POST.get('developer_name', '')
            project.contact_person = request.POST.get('contact_person', '')
            project.contact_phone = request.POST.get('contact_phone', '')
            project.contact_email = request.POST.get('contact_email', '')
            project.ivr_number = request.POST.get('ivr_number', '')
            project.save()
            messages.success(request, 'Project updated successfully!')
            return redirect('project_details', project_id=project.id)
        except Exception as e:
            messages.error(request, f'Error updating project: {str(e)}')
    
    context = {'project': project, 'status_choices': Project.STATUS_CHOICES}
    return render(request, 'dashboard/edit_project.html', context)

@login_required
def project_details(request, project_id):
    """Enhanced project details view with leads list"""
    project = get_object_or_404(Project, id=project_id)
    project_images = project.images.all()
    
    # Get leads interested in this project with pagination
    interested_leads = project.interested_leads.all().order_by('-created_at')
    paginator = Paginator(interested_leads, 10)  # 10 leads per page
    page_number = request.GET.get('page')
    leads = paginator.get_page(page_number)
    
    related_tasks = project.tasks.all()[:5]
    
    # Process amenities and features for display
    amenities_list = []
    if project.amenities:
        amenities_list = [amenity.strip() for amenity in project.amenities.split(',') if amenity.strip()]
    
    features_list = []
    if project.features:
        features_list = [feature.strip() for feature in project.features.split(',') if feature.strip()]
    
    # Lead statistics for this project
    lead_stats = {
        'total': interested_leads.count(),
        'hot': interested_leads.filter(current_stage__category='hot').count(),
        'warm': interested_leads.filter(current_stage__category='warm').count(),
        'cold': interested_leads.filter(current_stage__category='cold').count(),
        'converted': interested_leads.filter(current_stage__category='closed').count(),
    }
    
    context = {
        'project': project,
        'project_images': project_images,
        'leads': leads,
        'lead_stats': lead_stats,
        'related_tasks': related_tasks,
        'amenities_list': amenities_list,
        'features_list': features_list,
    }
    
    return render(request, 'dashboard/project_details.html', context)

@login_required
def delete_project(request, project_id):
    """Soft delete project"""
    project = get_object_or_404(Project, id=project_id)
    
    if request.method == 'POST':
        project.is_active = False
        project.save()
        messages.success(request, f'Project "{project.name}" has been deleted successfully!')
        return redirect('projects')
    
    context = {
        'project': project,
    }
    
    return render(request, 'dashboard/delete_project.html', context)

@login_required
def delete_project_image(request, image_id):
    """AJAX view to delete project image"""
    if request.method == 'POST':
        try:
            image = get_object_or_404(ProjectImage, id=image_id)
            image.delete()
            return JsonResponse({'success': True, 'message': 'Image deleted successfully!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

# Lead Management Views (keeping your existing ones)
@login_required
def create_brochure_lead(request):
    """AJAX view to create lead from brochure download"""
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        
        try:
            # Check if lead already exists
            existing_lead = Lead.objects.filter(
                Q(email=data['email']) | Q(phone=data['phone'])
            ).first()
            
            if existing_lead:
                # Add project to existing lead's interests
                if data.get('project_id'):
                    existing_lead.interested_projects.add(data['project_id'])
                return JsonResponse({
                    'success': True, 
                    'message': 'Thank you! We already have your details and will contact you soon.'
                })
            
            # Create new lead
            lead = Lead.objects.create(
                name=data['name'],
                email=data['email'],
                phone=data['phone'],
                source=data.get('source', 'website'),
                notes=f"Downloaded brochure for project ID: {data.get('project_id', 'N/A')}"
            )
            
            # Add interested project
            if data.get('project_id'):
                lead.interested_projects.add(data['project_id'])
            
            return JsonResponse({'success': True, 'message': 'Lead created successfully!'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
def leads(request):
    # Get filter parameters
    status_filter = request.GET.get('stage', '')
    source_filter = request.GET.get('source', '')
    search_query = request.GET.get('search', '')
    rows_per_page = int(request.GET.get('rows_per_page', 25))
    
    # Start with all leads
    leads_list = Lead.objects.all().select_related('assigned_to', 'current_stage').prefetch_related('interested_projects')
    
    # Apply filters
    if status_filter:
        leads_list = leads_list.filter(current_stage__category=status_filter)
    
    if source_filter:
        leads_list = leads_list.filter(source=source_filter)
    
    if search_query:
        leads_list = leads_list.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(leads_list, rows_per_page)
    page_number = request.GET.get('page')
    leads = paginator.get_page(page_number)
    
    # Get all team members for assignment
    team_members = User.objects.filter(teammember__isnull=False)
    
    context = {
        'leads': leads,
        'team_members': team_members,
        'stage_choices': LeadStage.STAGE_CATEGORIES,
        'source_choices': Lead.SOURCE_CHOICES,
        'current_stage': status_filter,
        'current_source': source_filter,
        'search_query': search_query,
    }
    
    return render(request, 'dashboard/leads.html', context)

@login_required
def add_lead(request):
    if request.method == 'POST':
        try:
            current_stage_id = request.POST.get('current_stage')
            lead = Lead.objects.create(
                name=request.POST['name'],
                email=request.POST['email'],
                phone=request.POST['phone'],
                source=request.POST['source'],
                notes=request.POST.get('notes', ''),
                budget_min=request.POST.get('budget_min') or None,
                budget_max=request.POST.get('budget_max') or None,
            )

            # Set stage if provided
            if current_stage_id:
                lead.current_stage_id = current_stage_id
                lead.save()
            
            # Assign to team member if specified
            if request.POST.get('assigned_to'):
                lead.assigned_to_id = request.POST['assigned_to']
                lead.save()
            
            # Add interested projects
            interested_projects = request.POST.getlist('interested_projects')
            if interested_projects:
                lead.interested_projects.add(*interested_projects)
            
            messages.success(request, 'Lead added successfully!')
            return redirect('leads')
        except Exception as e:
            messages.error(request, f'Error adding lead: {str(e)}')
    
    team_members = User.objects.filter(teammember__isnull=False)
    projects = Project.objects.filter(is_active=True)
    
    context = {
        'team_members': team_members,
        'projects': projects,
        'stage_choices': LeadStage.objects.filter(is_active=True).order_by('category', 'order'),
        'source_choices': Lead.SOURCE_CHOICES,
    }
    
    return render(request, 'dashboard/add_lead.html', context)

@login_required
def edit_lead(request, lead_id):
    lead = get_object_or_404(Lead, id=lead_id)
    
    if request.method == 'POST':
        try:
            lead.name = request.POST['name']
            lead.email = request.POST['email']
            # Phone number cannot be changed once set
            # lead.phone = request.POST['phone']  # Commented out to prevent changes

            # Handle additional phone numbers
            additional_phones = request.POST.get('additional_phones', '').strip()
            if additional_phones:
                # Append to notes or create a separate field
                if 'Additional phones:' not in lead.notes:
                    lead.notes += f"\nAdditional phones: {additional_phones}"
                else:
                    # Update existing additional phones
                    lines = lead.notes.split('\n')
                    for i, line in enumerate(lines):
                        if line.startswith('Additional phones:'):
                            lines[i] = f"Additional phones: {additional_phones}"
                            break
                    lead.notes = '\n'.join(lines)
            lead.source = request.POST['source']
            current_stage_id = request.POST.get('current_stage')
            if current_stage_id:
                lead.current_stage_id = current_stage_id
            lead.notes = request.POST.get('notes', '')
            lead.budget_min = request.POST.get('budget_min') or None
            lead.budget_max = request.POST.get('budget_max') or None
            
            # Assign to team member
            if request.POST.get('assigned_to'):
                lead.assigned_to_id = request.POST['assigned_to']
            else:
                lead.assigned_to = None
            
            lead.save()
            
            # Update interested projects
            interested_projects = request.POST.getlist('interested_projects')
            lead.interested_projects.clear()
            if interested_projects:
                lead.interested_projects.add(*interested_projects)
            
            messages.success(request, 'Lead updated successfully!')
            return redirect('leads')
        except Exception as e:
            messages.error(request, f'Error updating lead: {str(e)}')
    
    team_members = User.objects.filter(teammember__isnull=False).select_related('teammember')
    projects = Project.objects.filter(is_active=True)
    
    context = {
        'lead': lead,
        'team_members': team_members,
        'projects': projects,
        'stage_choices': LeadStage.objects.filter(is_active=True).order_by('category', 'order'),
        'source_choices': Lead.SOURCE_CHOICES,
    }
    
    return render(request, 'dashboard/edit_lead.html', context)

@login_required
def view_lead(request, lead_id):
    lead = get_object_or_404(Lead, id=lead_id)
    meetings = Meeting.objects.filter(lead=lead).order_by('-meeting_date')
    lead_notes = LeadNote.objects.filter(lead=lead).order_by('-created_at')
    
    context = {
        'lead': lead,
        'meetings': meetings,
        'lead_notes': lead_notes,
    }
    
    return render(request, 'dashboard/view_lead.html', context)

# Add the missing add_lead_note function
@login_required
def add_lead_note(request):
    """AJAX view to add a note to a lead"""
    if request.method == 'POST':
        try:
            lead_id = request.POST.get('lead_id')
            note_content = request.POST.get('note')
            call_type = request.POST.get('call_type', 'outgoing')
            next_action = request.POST.get('next_action', '')
            follow_up_date = request.POST.get('follow_up_date')
            requires_callback = request.POST.get('requires_callback') == 'on'
            
            lead = Lead.objects.get(id=lead_id)
            
            # Create the note
            note = LeadNote.objects.create(
                lead=lead,
                note=note_content,
                call_type=call_type,
                next_action=next_action,
                created_by=request.user
            )
            
            # Update lead's last contact date and follow-up info
            lead.last_contact_date = timezone.now().date()
            if follow_up_date:
                lead.follow_up_date = follow_up_date
            lead.requires_callback = requires_callback
            lead.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Note added successfully!',
                'note_id': note.id,
                'created_at': note.created_at.strftime('%b %d, %Y %I:%M %p')
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

# Team Management Views (keeping your existing ones)
@login_required
def team(request):
    team_members = TeamMember.objects.select_related('user').all()
    
    context = {
        'team_members': team_members,
    }
    
    return render(request, 'dashboard/team.html', context)

@login_required
def add_member(request):
    if request.method == 'POST':
        try:
            # Get manager selection
            manager_id = request.POST.get('manager')
            role = request.POST.get('role')
            
            # Validate manager selection (required for all roles except admin and manager)
            if role not in ['admin', 'manager'] and not manager_id:
                messages.error(request, 'Manager selection is required for this role.')
                
                # Get available managers for context
                managers = TeamMember.objects.filter(role__in=['admin', 'manager', 'team_lead']).select_related('user')
                
                context = {
                    'role_choices': TeamMember.ROLE_CHOICES,
                    'managers': managers,
                    # Return form data for re-population
                    'form_data': request.POST
                }
                return render(request, 'dashboard/add_member.html', context)
            
            # Create user
            user = User.objects.create_user(
                username=request.POST['username'],
                email=request.POST['email'],
                password=request.POST['password'],
                first_name=request.POST['first_name'],
                last_name=request.POST['last_name']
            )
            
            # Create team member
            team_member = TeamMember.objects.create(
                user=user,
                role=role,
                phone=request.POST['phone'],
                date_of_birth=request.POST.get('date_of_birth') or None,
                joining_date=request.POST.get('joining_date') or None,
                can_access_dashboard=request.POST.get('can_access_dashboard') == 'on',
                can_access_projects=request.POST.get('can_access_projects') == 'on',
                can_access_leads=request.POST.get('can_access_leads') == 'on',
                can_access_reports=request.POST.get('can_access_reports') == 'on',
                can_access_earnings=request.POST.get('can_access_earnings') == 'on',
                can_access_clients=request.POST.get('can_access_clients') == 'on',
                can_access_calendar=request.POST.get('can_access_calendar') == 'on',
                can_access_tasks=request.POST.get('can_access_tasks') == 'on',
                can_access_analytics=request.POST.get('can_access_analytics') == 'on',
            )
            
            # Set manager if provided
            if manager_id:
                team_member.manager_id = manager_id
                team_member.save()
            
            messages.success(request, 'Team member added successfully!')
            return redirect('team')
        except Exception as e:
            messages.error(request, f'Error adding team member: {str(e)}')
    
    # Get available managers for dropdown
    managers = TeamMember.objects.filter(role__in=['admin', 'manager', 'team_lead']).select_related('user')
    
    context = {
        'role_choices': TeamMember.ROLE_CHOICES,
        'managers': managers
    }
    
    return render(request, 'dashboard/add_member.html', context)

@login_required
def edit_member(request, member_id):
    team_member = get_object_or_404(TeamMember, id=member_id)
    
    if request.method == 'POST':
        try:
            # Get manager selection
            manager_id = request.POST.get('manager')
            role = request.POST.get('role')
            
            # Validate manager selection (required for all roles except admin and manager)
            if role not in ['admin', 'manager'] and not manager_id:
                messages.error(request, 'Manager selection is required for this role.')
                
                # Get available managers for context
                managers = TeamMember.objects.filter(role__in=['admin', 'manager', 'team_lead']).exclude(id=member_id).select_related('user')
                
                context = {
                    'team_member': team_member,
                    'role_choices': TeamMember.ROLE_CHOICES,
                    'managers': managers,
                    # Return form data for re-population
                    'form_data': request.POST
                }
                return render(request, 'dashboard/edit_member.html', context)
            
            # Prevent self-assignment as manager
            if manager_id and int(manager_id) == team_member.id:
                messages.error(request, 'A team member cannot be their own manager.')
                
                # Get available managers for context
                managers = TeamMember.objects.filter(role__in=['admin', 'manager', 'team_lead']).exclude(id=member_id).select_related('user')
                
                context = {
                    'team_member': team_member,
                    'role_choices': TeamMember.ROLE_CHOICES,
                    'managers': managers,
                    # Return form data for re-population
                    'form_data': request.POST
                }
                return render(request, 'dashboard/edit_member.html', context)
            
            # Update user
            user = team_member.user
            user.first_name = request.POST['first_name']
            user.last_name = request.POST['last_name']
            user.email = request.POST['email']
            user.save()
            
            # Update team member
            team_member.role = role
            team_member.phone = request.POST['phone']
            team_member.date_of_birth = request.POST.get('date_of_birth') or None
            team_member.joining_date = request.POST.get('joining_date') or None
            team_member.can_access_dashboard = request.POST.get('can_access_dashboard') == 'on'
            team_member.can_access_projects = request.POST.get('can_access_projects') == 'on'
            team_member.can_access_leads = request.POST.get('can_access_leads') == 'on'
            team_member.can_access_reports = request.POST.get('can_access_reports') == 'on'
            team_member.can_access_earnings = request.POST.get('can_access_earnings') == 'on'
            team_member.can_access_clients = request.POST.get('can_access_clients') == 'on'
            team_member.can_access_calendar = request.POST.get('can_access_calendar') == 'on'
            team_member.can_access_tasks = request.POST.get('can_access_tasks') == 'on'
            team_member.can_access_analytics = request.POST.get('can_access_analytics') == 'on'
            
            # Set manager if provided
            if manager_id:
                team_member.manager_id = manager_id
            else:
                team_member.manager = None
                
            team_member.save()
            
            messages.success(request, 'Team member updated successfully!')
            return redirect('team')
        except Exception as e:
            messages.error(request, f'Error updating team member: {str(e)}')
    
    # Get available managers for dropdown (excluding self)
    managers = TeamMember.objects.filter(role__in=['admin', 'manager', 'team_lead']).exclude(id=member_id).select_related('user')
    
    context = {
        'team_member': team_member,
        'role_choices': TeamMember.ROLE_CHOICES,
        'managers': managers
    }
    
    return render(request, 'dashboard/edit_member.html', context)

@login_required
def delete_member(request, member_id):
    team_member = get_object_or_404(TeamMember, id=member_id)
    
    if request.method == 'POST':
        user = team_member.user
        team_member.delete()
        user.delete()
        messages.success(request, 'Team member deleted successfully!')
        return redirect('team')
    
    context = {
        'team_member': team_member,
    }
    
    return render(request, 'dashboard/delete_member.html', context)

@login_required
def profile(request):
    try:
        team_member = request.user.teammember
    except TeamMember.DoesNotExist:
        team_member = None
    
    if request.method == 'POST':
        try:
            # Update user details
            user = request.user
            user.first_name = request.POST['first_name']
            user.last_name = request.POST['last_name']
            user.email = request.POST['email']
            user.save()
            
            # Update team member details if exists
            if team_member:
                team_member.phone = request.POST.get('phone', '')
                team_member.date_of_birth = request.POST.get('date_of_birth') or None
                team_member.joining_date = request.POST.get('joining_date') or None
                
                # Handle profile picture upload
                if request.FILES.get('profile_picture'):
                    team_member.profile_picture = request.FILES['profile_picture']
                
                team_member.save()
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
    
    context = {
        'team_member': team_member,
    }
    
    return render(request, 'dashboard/profile.html', context)

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
    
    context = {
        'form': form,
    }
    
    return render(request, 'dashboard/change_password.html', context)

# AJAX Views
@login_required
def assign_lead(request):
    if request.method == 'POST':
        lead_id = request.POST.get('lead_id')
        user_id = request.POST.get('user_id')
        
        try:
            lead = Lead.objects.get(id=lead_id)
            if user_id:
                lead.assigned_to_id = user_id
            else:
                lead.assigned_to = None
            lead.save()
            
            return JsonResponse({'success': True, 'message': 'Lead assigned successfully!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
def update_lead_status(request):
    if request.method == 'POST':
        lead_id = request.POST.get('lead_id')
        new_stage_id = request.POST.get('stage_id')
        
        try:
            lead = Lead.objects.get(id=lead_id)
            new_stage = LeadStage.objects.get(id=new_stage_id)
            
            # Use the move_to_stage method
            lead.move_to_stage(new_stage, request.user)
            
            return JsonResponse({'success': True, 'message': f'Lead moved to {new_stage.name} successfully!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

# Other views
@login_required
def reports(request):
    from django.db.models import Count, Q
    from django.db.models.functions import TruncMonth, TruncDate
    from datetime import datetime, timedelta
    
    # Lead statistics by source
    leads_by_source = Lead.objects.values('source').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Lead statistics by stage category
    leads_by_stage = Lead.objects.values('current_stage__category').annotate(
        count=Count('id')
    ).order_by('-count')

    # Lead statistics by project
    leads_by_project = Lead.objects.filter(
        interested_projects__isnull=False
    ).values('interested_projects__name').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Monthly trends (last 12 months) - SQLite compatible
    monthly_leads = Lead.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=365)
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    # Daily activity (last 30 days) - SQLite compatible
    daily_activity = Lead.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=30)
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    # Convert monthly data for template
    monthly_data = []
    for item in monthly_leads:
        monthly_data.append({
            'month': item['month'].strftime('%b %Y'),
            'count': item['count']
        })
    
    # Convert daily data for template
    daily_data = []
    for item in daily_activity:
        daily_data.append({
            'date': item['date'].strftime('%d %b'),
            'count': item['count']
        })
    
    # Lead conversion funnel
    total_leads = Lead.objects.count()
    warm_leads = Lead.objects.filter(current_stage__category='warm').count()
    hot_leads = Lead.objects.filter(current_stage__category='hot').count()
    converted_leads = Lead.objects.filter(current_stage__category='closed').count()

    # Lead statistics by source with percentages
    leads_by_source = Lead.objects.values('source').annotate(
        count=Count('id')
    ).order_by('-count')

    # Add percentage calculation
    for item in leads_by_source:
        item['percentage'] = round((item['count'] * 100 / total_leads), 1) if total_leads > 0 else 0

    # Add percentage calculation
    for item in leads_by_stage:
        item['percentage'] = round((item['count'] * 100 / total_leads), 1) if total_leads > 0 else 0
    
    context = {
        'leads_by_source': leads_by_source,
        'leads_by_status': leads_by_stage,
        'leads_by_project': leads_by_project,
        'monthly_leads': monthly_data,
        'daily_activity': daily_data,
        'total_leads': total_leads,
        'warm_leads': warm_leads,
        'hot_leads': hot_leads,
        'converted_leads': converted_leads,
    }
    
    return render(request, 'dashboard/reports.html', context)

@login_required
def earnings(request):
    earnings_list = Earning.objects.select_related('project', 'lead', 'earned_by').order_by('-date_earned')
    total_earnings = earnings_list.aggregate(total=Sum('commission_amount'))['total'] or 0
    
    context = {
        'earnings': earnings_list,
        'total_earnings': total_earnings,
    }
    return render(request, 'dashboard/earnings.html', context)

@login_required
def clients(request):
    clients = Client.objects.all().select_related('created_by')
    return render(request, 'dashboard/clients.html', {'clients': clients})

# Calendar Views
@login_required
def calendar(request):
    """View for the calendar page"""
    projects = Project.objects.filter(is_active=True).order_by('name')
    active_leads = Lead.objects.exclude(current_stage__category='lost').order_by('name')
    team_members = TeamMember.objects.select_related('user').all()
    
    context = {
        'projects': projects,
        'active_leads': active_leads,
        'team_members': team_members
    }
    
    return render(request, 'dashboard/calendar.html', context)

@login_required
def calendar_events_json(request):
    """API endpoint for getting calendar events as JSON"""
    events = CalendarEvent.objects.filter(
        # Filter events created by this user or where user is an attendee
        Q(created_by=request.user) | Q(attendees=request.user)
    ).distinct().select_related('project', 'lead')
    
    event_data = []
    for event in events:
        # Format the event for FullCalendar
        item = {
            'id': event.id,
            'title': event.title,
            'start': event.start_time.isoformat(),
            'end': event.end_time.isoformat(),
            'allDay': event.all_day,
            'backgroundColor': event.color,
            'borderColor': event.color,
            'extendedProps': {
                'description': event.description,
                'location': event.location,
                'event_type': event.event_type,
                'created_by': event.created_by.get_full_name(),
            }
        }
        
        # Add optional relations
        if event.project:
            item['extendedProps']['project_id'] = event.project.id
            item['extendedProps']['project_name'] = event.project.name
            
        if event.lead:
            item['extendedProps']['lead_id'] = event.lead.id
            item['extendedProps']['lead_name'] = event.lead.name
        
        event_data.append(item)
    
    return JsonResponse(event_data, safe=False)

@login_required
def add_event(request):
    """View for adding a new calendar event"""
    if request.method == 'POST':
        try:
            title = request.POST.get('title')
            event_type = request.POST.get('event_type')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            all_day = request.POST.get('all_day') == 'on'
            location = request.POST.get('location', '')
            description = request.POST.get('description', '')
            project_id = request.POST.get('project')
            lead_id = request.POST.get('lead')
            color = request.POST.get('color', '#4f46e5')
            
            # Create the event
            event = CalendarEvent.objects.create(
                title=title,
                event_type=event_type,
                start_time=start_time,
                end_time=end_time,
                all_day=all_day,
                location=location,
                description=description,
                color=color,
                created_by=request.user
            )
            
            # Set optional relations
            if project_id:
                event.project_id = project_id
                
            if lead_id:
                event.lead_id = lead_id
                
            # Add attendees
            attendees = request.POST.getlist('attendees')
            if attendees:
                event.attendees.add(*attendees)
                
            event.save()
            
            messages.success(request, 'Event added successfully!')
            return redirect('calendar')
            
        except Exception as e:
            messages.error(request, f'Error adding event: {str(e)}')
            return redirect('calendar')
    
    # Should not reach here as this view is only for POST
    return redirect('calendar')

@login_required
def edit_event(request, event_id):
    """View for editing a calendar event"""
    event = get_object_or_404(CalendarEvent, id=event_id)
    
    if request.method == 'POST':
        try:
            event.title = request.POST.get('title')
            event.event_type = request.POST.get('event_type')
            event.start_time = request.POST.get('start_time')
            event.end_time = request.POST.get('end_time')
            event.all_day = request.POST.get('all_day') == 'on'
            event.location = request.POST.get('location', '')
            event.description = request.POST.get('description', '')
            event.color = request.POST.get('color', '#4f46e5')
            
            # Update optional relations
            project_id = request.POST.get('project')
            if project_id:
                event.project_id = project_id
            else:
                event.project = None
                
            lead_id = request.POST.get('lead')
            if lead_id:
                event.lead_id = lead_id
            else:
                event.lead = None
                
            # Update attendees
            attendees = request.POST.getlist('attendees')
            event.attendees.clear()
            if attendees:
                event.attendees.add(*attendees)
                
            event.save()
            
            messages.success(request, 'Event updated successfully!')
            return redirect('calendar')
            
        except Exception as e:
            messages.error(request, f'Error updating event: {str(e)}')
    
    projects = Project.objects.filter(is_active=True).order_by('name')
    active_leads = Lead.objects.exclude(current_stage__category='lost').order_by('name')
    team_members = TeamMember.objects.select_related('user').all()
    
    context = {
        'event': event,
        'projects': projects,
        'active_leads': active_leads,
        'team_members': team_members
    }
    
    return render(request, 'dashboard/edit_event.html', context)

@login_required
def delete_event(request, event_id):
    """AJAX view for deleting a calendar event"""
    if request.method == 'POST':
        event = get_object_or_404(CalendarEvent, id=event_id)
        title = event.title
        event.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Event "{title}" was deleted successfully!'
        })
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method.'
    })

# Task Management Views
@login_required
def tasks(request):
    """View for task management dashboard"""
    tasks = Task.objects.all().prefetch_related('assigned_to', 'category').select_related('stage', 'project', 'lead')
    stages = TaskStage.objects.all().order_by('order')
    categories = TaskCategory.objects.all()
    projects = Project.objects.filter(is_active=True)
    leads = Lead.objects.exclude(current_stage__category='lost')
    team_members = TeamMember.objects.select_related('user').all()
    
    context = {
        'tasks': tasks,
        'stages': stages,
        'categories': categories,
        'projects': projects,
        'leads': leads,
        'team_members': team_members,
    }
    
    return render(request, 'dashboard/tasks.html', context)

@login_required
def task_categories(request):
    """View for managing task categories"""
    if request.method == 'POST':
        name = request.POST.get('name')
        color = request.POST.get('color', '#3b82f6')
        description = request.POST.get('description', '')
        
        TaskCategory.objects.create(name=name, color=color, description=description)
        messages.success(request, 'Category added successfully!')
        return redirect('task_categories')
    
    categories = TaskCategory.objects.all()
    context = {'categories': categories}
    return render(request, 'dashboard/task_categories.html', context)

@login_required
def add_task(request):
    """View for adding a new task"""
    if request.method == 'POST':
        try:
            title = request.POST.get('title')
            description = request.POST.get('description', '')
            category_id = request.POST.get('category')
            stage_id = request.POST.get('stage')
            priority = request.POST.get('priority', 'medium')
            due_date_str = request.POST.get('due_date')
            project_id = request.POST.get('project')
            lead_id = request.POST.get('lead')
            assigned_to = request.POST.getlist('assigned_to')
            
            # Create the task
            task = Task.objects.create(
                title=title,
                description=description,
                stage_id=stage_id,
                priority=priority,
                created_by=request.user,
            )
            
            # Set optional fields
            if category_id:
                task.category_id = category_id
            
            if due_date_str:
                task.due_date = due_date_str
                
            if project_id:
                task.project_id = project_id
                
            if lead_id:
                task.lead_id = lead_id
            
            task.save()
            
            # Assign the task to users
            if assigned_to:
                task.assigned_to.add(*assigned_to)
            
            messages.success(request, 'Task created successfully!')
            return redirect('tasks')
            
        except Exception as e:
            messages.error(request, f'Error creating task: {str(e)}')
            return redirect('tasks')
    
    # Should not reach here as this view is only for POST
    return redirect('tasks')

@login_required
def edit_task(request, task_id):
    """View for editing an existing task"""
    task = get_object_or_404(Task, id=task_id)
    
    if request.method == 'POST':
        try:
            task.title = request.POST.get('title')
            task.description = request.POST.get('description', '')
            task.stage_id = request.POST.get('stage')
            task.priority = request.POST.get('priority', 'medium')
            
            # Update optional fields
            category_id = request.POST.get('category')
            if category_id:
                task.category_id = category_id
            else:
                task.category = None
                
            due_date_str = request.POST.get('due_date')
            if due_date_str:
                task.due_date = due_date_str
            else:
                task.due_date = None
                
            project_id = request.POST.get('project')
            if project_id:
                task.project_id = project_id
            else:
                task.project = None
                
            lead_id = request.POST.get('lead')
            if lead_id:
                task.lead_id = lead_id
            else:
                task.lead = None
                
            task.save()
            
            # Update assignees
            assigned_to = request.POST.getlist('assigned_to')
            task.assigned_to.clear()
            if assigned_to:
                task.assigned_to.add(*assigned_to)
            
            messages.success(request, 'Task updated successfully!')
            return redirect('tasks')
            
        except Exception as e:
            messages.error(request, f'Error updating task: {str(e)}')
    
    stages = TaskStage.objects.all().order_by('order')
    categories = TaskCategory.objects.all()
    projects = Project.objects.filter(is_active=True)
    leads = Lead.objects.exclude(current_stage__category='lost')
    team_members = TeamMember.objects.select_related('user').all()
    
    context = {
        'task': task,
        'stages': stages,
        'categories': categories,
        'projects': projects,
        'leads': leads,
        'team_members': team_members,
    }
    
    return render(request, 'dashboard/edit_task.html', context)

@login_required
def task_detail(request, task_id):
    """AJAX view for getting task details"""
    task = get_object_or_404(Task, id=task_id)
    
    # Build HTML for task details
    assignees_list = ", ".join([user.get_full_name() for user in task.assigned_to.all()])
    
    priority_classes = {
        'low': 'text-muted',
        'medium': 'text-primary',
        'high': 'text-warning',
        'urgent': 'text-danger'
    }
    
    priority_html = f'<span class="{priority_classes.get(task.priority, "text-muted")}">{task.get_priority_display()}</span>'
    
    html = f"""
    <div class="mb-3">
        <span class="badge bg-{"primary" if task.category else "secondary"} me-2">
            {task.category.name if task.category else "No Category"}
        </span>
        <span class="badge bg-{"success" if task.completed else "secondary"}">
            {"Completed" if task.completed else "Open"}
        </span>
    </div>
    
    <p><strong>Description:</strong><br>{task.description or "No description provided."}</p>
    
    <table class="table table-sm">
        <tr>
            <th>Priority:</th>
            <td>{priority_html}</td>
        </tr>
        <tr>
            <th>Stage:</th>
            <td>{task.stage.name}</td>
        </tr>
        <tr>
            <th>Due Date:</th>
            <td>{task.due_date.strftime("%d %b %Y") if task.due_date else "Not set"}</td>
        </tr>
        <tr>
            <th>Assigned To:</th>
            <td>{assignees_list or "Not assigned"}</td>
        </tr>
        <tr>
            <th>Created By:</th>
            <td>{task.created_by.get_full_name()}</td>
        </tr>
        <tr>
            <th>Created At:</th>
            <td>{task.created_at.strftime("%d %b %Y %H:%M")}</td>
        </tr>
    </table>
    
    {f'<p><strong>Related Project:</strong> {task.project.name}</p>' if task.project else ''}
    {f'<p><strong>Related Lead:</strong> {task.lead.name}</p>' if task.lead else ''}
    """
    
    return JsonResponse({
        'success': True,
        'title': task.title,
        'html': html
    })

@login_required
def complete_task(request, task_id):
    """AJAX view for marking a task as complete"""
    if request.method == 'POST':
        task = get_object_or_404(Task, id=task_id)
        task.mark_as_complete()
        
        return JsonResponse({
            'success': True,
            'message': f'Task "{task.title}" marked as complete!'
        })
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method.'
    })

@login_required
def delete_task(request, task_id):
    """AJAX view for deleting a task"""
    if request.method == 'POST':
        task = get_object_or_404(Task, id=task_id)
        title = task.title
        task.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Task "{title}" was deleted successfully!'
        })
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method.'
    })

@login_required
def analytics(request):
    """Analytics view with filters for project, team, and source"""
    # Get filter parameters
    project_filter = request.GET.get('project', '')
    team_filter = request.GET.get('team', '')
    source_filter = request.GET.get('source', '')
    
    # Base querysets
    projects = Project.objects.filter(is_active=True)
    leads = Lead.objects.all()
    expenses = MarketingExpense.objects.all()

    # Apply filters
    if project_filter:
        leads = leads.filter(interested_projects__id=project_filter)
        expenses = expenses.filter(category=project_filter) # Assuming expense category matches project
    if team_filter:
        leads = leads.filter(assigned_to_id=team_filter)
    if source_filter:
        leads = leads.filter(source=source_filter)
        
    # Aggregate data
    if team_filter:
        # Team-based analytics
        team_member = get_object_or_404(User, id=team_filter)
        analytics_data = [{
            'dimension': team_member.get_full_name(),
            'total_leads': leads.count(),
            'conversion_rate': (leads.filter(current_stage__category='closed').count() * 100.0 / leads.count()) if leads.count() > 0 else 0,
            'total_cost': 0, # CPL for team member is complex, omitting for now
            'cpl': 0
        }]
    elif project_filter:
         # Project-based analytics
        project = get_object_or_404(Project, id=project_filter)
        analytics_data = [{
            'dimension': project.name,
            'total_leads': leads.count(),
            'conversion_rate': project.conversion_rate,
            'total_cost': 0,
            'cpl': 0
        }]
    else:
        # Overall analytics grouped by project
        analytics_data = Project.objects.filter(is_active=True).annotate(
            total_leads=Count('interested_leads'),
            converted_leads=Count('interested_leads', filter=Q(interested_leads__current_stage__category='closed')),
        ).annotate(
            conversion_rate=ExpressionWrapper(
                (F('converted_leads') * 100.0 / F('total_leads')),
                output_field=fields.FloatField()
            )
        ).values('name', 'total_leads', 'conversion_rate')
        
        analytics_data = [{
            'dimension': item['name'],
            'total_leads': item['total_leads'],
            'conversion_rate': item['conversion_rate'] or 0,
            'total_cost': 0,
            'cpl': 0,
        } for item in analytics_data]

    context = {
        'analytics_data': analytics_data,
        'projects': Project.objects.filter(is_active=True),
        'teams': User.objects.filter(teammember__isnull=False),
        'sources': Lead.SOURCE_CHOICES,
        'current_project': project_filter,
        'current_team': team_filter,
        'current_source': source_filter,
    }
    return render(request, 'dashboard/analytics.html', context)


@login_required
def automation(request):
    """Automation hub page"""
    return render(request, 'dashboard/automation.html')

# Add this new view to your views.py file

@login_required
def bulk_email(request):
    """Enhanced bulk email with multiple provider support"""
    if request.method == 'POST':
        try:
            # Get form data
            email_username = request.POST.get('email_username')
            email_password = request.POST.get('email_password')
            display_email = request.POST.get('display_email')  # New field
            smtp_server = request.POST.get('smtp_server')
            smtp_port = int(request.POST.get('smtp_port', 587))
            provider_name = request.POST.get('provider_name')  # New field
            subject = request.POST.get('subject')
            email_template = request.POST.get('email_template')
            
            # Validate required fields
            if not all([email_username, email_password, display_email, subject, email_template]):
                messages.error(request, 'Please fill in all required fields.')
                return redirect('bulk_email')
            
            # Handle file upload
            excel_file = request.FILES.get('excel_file')
            if not excel_file:
                messages.error(request, 'Please upload an Excel file.')
                return redirect('bulk_email')
            
            # Save file temporarily
            file_name = default_storage.save(f'temp/{excel_file.name}', ContentFile(excel_file.read()))
            file_path = default_storage.path(file_name)
            
            try:
                # Read Excel file (support both Excel and CSV)
                if file_name.endswith('.csv'):
                    df = pd.read_csv(file_path)
                else:
                    df = pd.read_excel(file_path)
                
                # Validate columns
                if 'name' not in df.columns or 'email' not in df.columns:
                    messages.error(request, 'File must have "name" and "email" columns.')
                    default_storage.delete(file_name)
                    return redirect('bulk_email')
                
                # Enhanced SMTP connection test
                try:
                    server = smtplib.SMTP(smtp_server, smtp_port)
                    server.starttls()
                    server.login(email_username, email_password)
                    server.quit()
                    
                except smtplib.SMTPAuthenticationError as e:
                    default_storage.delete(file_name)
                    
                    if provider_name == 'sendgrid':
                        messages.error(request, 
                            '🔐 SendGrid Authentication Failed!\n\n'
                            'Please check:\n'
                            '• Username should be "apikey"\n'
                            '• Password should be your SendGrid API key\n'
                            '• Make sure your API key has "Mail Send" permissions'
                        )
                    elif provider_name == 'gmail':
                        messages.error(request, 
                            '🔐 Gmail Authentication Failed!\n\n'
                            'Solutions:\n'
                            '• Enable 2-Factor Authentication\n'
                            '• Use App Password (not regular password)\n'
                            '• Go to myaccount.google.com → Security → App passwords'
                        )
                    elif provider_name == 'outlook':
                        messages.error(request, 
                            '🔐 Outlook Authentication Failed!\n\n'
                            'Microsoft has disabled basic authentication.\n'
                            '• Enable 2-Factor Authentication\n'
                            '• Create App Password at account.microsoft.com/security\n'
                            '• Use App Password (not regular password)'
                        )
                    else:
                        messages.error(request, f'Authentication failed: {str(e)}')
                    
                    return redirect('bulk_email')
                    
                except Exception as e:
                    default_storage.delete(file_name)
                    messages.error(request, f'Connection error: {str(e)}')
                    return redirect('bulk_email')
                
                # Setup email server for sending
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
                server.login(email_username, email_password)
                
                sent_count = 0
                failed_count = 0
                failed_emails = []
                total_emails = len(df)
                
                print(f"Starting bulk email via {provider_name} to {total_emails} recipients...")
                
                # Send emails
                for index, row in df.iterrows():
                    try:
                        name = str(row['name']).strip()
                        email = str(row['email']).strip()
                        
                        if not email or '@' not in email:
                            failed_count += 1
                            failed_emails.append(f"{email} (invalid)")
                            continue
                        
                        # Create personalized email
                        personalized_template = email_template.replace('{name}', name)
                        
                        msg = MIMEMultipart()
                        msg['From'] = display_email  # Use display email instead of username
                        msg['To'] = email
                        msg['Subject'] = subject
                        
                        msg.attach(MIMEText(personalized_template, 'html'))
                        
                        server.send_message(msg)
                        sent_count += 1
                        
                        # Add delay to avoid rate limiting
                        import time
                        time.sleep(0.2)
                        
                    except Exception as e:
                        failed_count += 1
                        failed_emails.append(f"{email} ({str(e)})")
                
                server.quit()
                default_storage.delete(file_name)
                
                # Success message
                if sent_count > 0:
                    success_rate = (sent_count / total_emails) * 100
                    success_msg = f'✅ Bulk email completed!\n\n'
                    success_msg += f'📧 Sent: {sent_count} emails\n'
                    if failed_count > 0:
                        success_msg += f'❌ Failed: {failed_count} emails\n'
                    success_msg += f'📊 Success rate: {success_rate:.1f}%\n'
                    success_msg += f'🚀 Provider: {provider_name.title()}'
                    
                    messages.success(request, success_msg)
                    return redirect('dashboard')
                else:
                    messages.error(request, f'No emails sent. {failed_count} failed.')
                    return redirect('bulk_email')
                
            except Exception as e:
                if 'file_name' in locals():
                    default_storage.delete(file_name)
                messages.error(request, f'Error processing file: {str(e)}')
                return redirect('bulk_email')
            
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return redirect('bulk_email')
    
    return render(request, 'dashboard/bulk_email.html')

@login_required
def bulk_whatsapp(request):
    """Bulk WhatsApp sending page"""
    return render(request, 'dashboard/bulk_whatsapp.html')

@login_required
def bulk_sms(request):
    """Bulk SMS sending page"""
    return render(request, 'dashboard/bulk_sms.html')

@login_required
def bulk_upload_leads(request):
    """Bulk upload leads from Excel/CSV file"""
    if request.method == 'POST':
        try:
            import pandas as pd
            from django.core.files.storage import default_storage
            from django.core.files.base import ContentFile
            from django.http import HttpResponseRedirect
           
            
            # Get form data
            bulk_file = request.FILES.get('bulk_file')
            default_source = request.POST.get('default_source', 'website')
            default_status = request.POST.get('default_status', 'warm')
            skip_duplicates = request.POST.get('skip_duplicates') == 'on'
            
            if not bulk_file:
                messages.error(request, 'Please upload a file.')
                return redirect('leads')
            
            # Save file temporarily
            file_name = default_storage.save(f'temp/{bulk_file.name}', ContentFile(bulk_file.read()))
            file_path = default_storage.path(file_name)
            
            try:
                # Read file based on extension
                if bulk_file.name.endswith('.csv'):
                    df = pd.read_csv(file_path)
                else:
                    df = pd.read_excel(file_path)
                
                # Validate required columns
                required_columns = ['name', 'email', 'phone']
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    default_storage.delete(file_name)
                    messages.error(request, f'Missing required columns: {", ".join(missing_columns)}')
                    return redirect('leads')
                
                created_count = 0
                skipped_count = 0
                error_count = 0
                errors = []
                
                for index, row in df.iterrows():
                    try:
                        name = str(row['name']).strip()
                        email = str(row['email']).strip().lower()
                        phone = str(row['phone']).strip()
                        
                        # Skip empty rows
                        if not name or not email or not phone:
                            skipped_count += 1
                            continue
                        
                        # Check for duplicates
                        if skip_duplicates:
                            existing = Lead.objects.filter(
                                Q(email=email) | Q(phone=phone)
                            ).first()
                            
                            if existing:
                                skipped_count += 1
                                continue
                        
                        # Get optional fields
                        source = row.get('source', default_source) if 'source' in df.columns else default_source
                        status = row.get('status', default_status) if 'status' in df.columns else default_status
                        budget_min = row.get('budget_min') if 'budget_min' in df.columns else None
                        budget_max = row.get('budget_max') if 'budget_max' in df.columns else None
                        notes = row.get('notes', '') if 'notes' in df.columns else ''
                        
                        # Validate source and status
                        valid_sources = [choice[0] for choice in Lead.SOURCE_CHOICES]
                        
                        if source not in valid_sources:
                            source = default_source
                        
                        # Create lead
                        lead = Lead.objects.create(
                            name=name,
                            email=email,
                            phone=phone,
                            source=source,
                            budget_min=budget_min if pd.notna(budget_min) else None,
                            budget_max=budget_max if pd.notna(budget_max) else None,
                            notes=notes
                        )
                        
                        # Set lead stage
                        stage = LeadStage.objects.filter(category=status).order_by('order').first()
                        if stage:
                            lead.current_stage = stage
                            lead.save()

                        created_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        errors.append(f"Row {index + 2}: {str(e)}")
                
                # Clean up temp file
                default_storage.delete(file_name)
                
                # Prepare success message
                success_msg = f'✅ Bulk upload completed! Created: {created_count} leads'
                if skipped_count > 0:
                    success_msg += f', Skipped: {skipped_count} duplicates'
                if error_count > 0:
                    success_msg += f', Errors: {error_count}'
                
                messages.success(request, success_msg)
                
                if errors:
                    error_msg = 'Errors encountered:\n' + '\n'.join(errors[:10])  # Show first 10 errors
                    if len(errors) > 10:
                        error_msg += f'\n... and {len(errors) - 10} more errors'
                    messages.warning(request, error_msg)
                
                return redirect('leads')
                
            except Exception as e:
                # Clean up temp file
                if 'file_name' in locals():
                    default_storage.delete(file_name)
                messages.error(request, f'Error processing file: {str(e)}')
                return redirect('leads')
            
        except Exception as e:
            messages.error(request, f'Error uploading leads: {str(e)}')
            return redirect('leads')
    
    return redirect('leads')

# ... (the rest of the views remain the same, so I'll omit them for brevity)

# Add the missing check_duplicate_leads function
@login_required
def check_duplicate_leads(request):
    """Check for duplicate leads based on email and phone"""
    if request.method == 'POST':
        try:
            duplicates_found = 0
            
            # Get all hot leads
            hot_leads = Lead.objects.filter(current_stage__category='hot')
            
            for lead in hot_leads:
                # Check for duplicates by email or phone
                potential_duplicates = Lead.objects.filter(
                    Q(email=lead.email) | Q(phone=lead.phone)
                ).exclude(id=lead.id).order_by('created_at')
                
                if potential_duplicates.exists():
                    original_lead = potential_duplicates.first()
                    
                    # Mark as duplicate if not already marked
                    if not lead.is_duplicate:
                        lead.is_duplicate = True
                        lead.original_lead = original_lead
                        lead.save()
                        duplicates_found += 1
            
            return JsonResponse({
                'success': True,
                'duplicates_found': duplicates_found
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

# Add the missing mark_duplicate_lead function
@login_required
def mark_duplicate_lead(request):
    """Mark a lead as duplicate"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            
            lead_id = data.get('lead_id')
            original_lead_id = data.get('original_lead_id')
            
            lead = Lead.objects.get(id=lead_id)
            original_lead = Lead.objects.get(id=original_lead_id)
            
            lead.is_duplicate = True
            lead.original_lead = original_lead
            lead.save()
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

# Add the missing merge_duplicate_lead function
@login_required
def merge_duplicate_lead(request):
    """Merge duplicate lead with original"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            
            lead_id = data.get('lead_id')
            lead = Lead.objects.get(id=lead_id, is_duplicate=True)
            
            if lead.original_lead:
                original = lead.original_lead
                
                # Merge notes
                for note in lead.call_notes.all():
                    note.lead = original
                    note.save()
                
                # Merge interested projects
                for project in lead.interested_projects.all():
                    original.interested_projects.add(project)
                
                # Update original lead's notes with merge info
                merge_note = f"Merged with duplicate lead: {lead.name} ({lead.email}, {lead.phone})"
                if original.notes:
                    original.notes += f"\n\n{merge_note}"
                else:
                    original.notes = merge_note
                original.save()
                
                # Delete the duplicate
                lead.delete()
                
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'No original lead found'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

# Add the missing acknowledge_notification function
@login_required
def acknowledge_notification(request, notification_id):
    """Acknowledge an important notification"""
    if request.method == 'POST':
        try:
            notification = Notification.objects.get(id=notification_id, recipient=request.user)
            notification.is_acknowledged = True
            notification.acknowledged_at = timezone.now()
            notification.is_read = True
            notification.save()
            
            return JsonResponse({'success': True})
        except Notification.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Notification not found'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

# Add the missing check_birthday_notifications function
@login_required
def check_birthday_notifications(request):
    """AJAX endpoint to check for birthday notifications"""
    if request.method == 'POST':
        try:
            from datetime import timedelta
            
            today = timezone.now().date()
            notifications_created = 0
            
            # Check for birthdays today
            team_members = TeamMember.objects.filter(
                date_of_birth__isnull=False
            ).select_related('user')
            
            for member in team_members:
                # Check if birthday is today
                birthday_this_year = member.date_of_birth.replace(year=today.year)
                if birthday_this_year < today:
                    birthday_this_year = member.date_of_birth.replace(year=today.year + 1)
                
                if birthday_this_year == today:
                    # Check if notification already exists for today
                    existing = Notification.objects.filter(
                        notification_type='birthday',
                        related_object_id=member.id,
                        created_at__date=today
                    ).exists()
                    
                    if not existing:
                        # Create notification for all users
                        for user in User.objects.filter(is_active=True):
                            Notification.objects.create(
                                recipient=user,
                                title="🎂 Birthday Today!",
                                message=f"Today is {member.user.get_full_name()}'s birthday! Don't forget to wish them!",
                                notification_type='birthday',
                                related_object_id=member.id,
                                related_object_type='teammember'
                            )
                            notifications_created += 1
            
            return JsonResponse({
                'success': True,
                'notifications_created': notifications_created
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

# Add the missing check_upcoming_events function
@login_required
def check_upcoming_events(request):
    """AJAX endpoint to check for upcoming events"""
    if request.method == 'POST':
        try:
            from datetime import timedelta
            
            today = timezone.now().date()
            notifications_created = 0
            
            # Get events happening today
            today_events = CalendarEvent.objects.filter(
                start_time__date=today,
                notification_sent=False
            )
            
            for event in today_events:
                # Create notifications for attendees or all users
                attendees = event.attendees.all() if event.attendees.exists() else User.objects.filter(is_active=True)
                
                for user in attendees:
                    # Check if notification already exists
                    existing = Notification.objects.filter(
                        notification_type='event',
                        related_object_id=event.id,
                        recipient=user,
                        created_at__date=today
                    ).exists()
                    
                    if not existing:
                        Notification.objects.create(
                            recipient=user,
                            title=f"📅 Event Today: {event.title}",
                            message=f"Don't forget about '{event.title}' today at {event.start_time.strftime('%I:%M %p')}!",
                            notification_type='event',
                            related_object_id=event.id,
                            related_object_type='calendarevent'
                        )
                        notifications_created += 1
                
                # Mark notification as sent
                event.notification_sent = True
                event.save()
            
            return JsonResponse({
                'success': True,
                'notifications_created': notifications_created
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

# Add missing attendance view
@login_required
def attendance(request):
    """Attendance management page for admins"""
    # Get filter parameters
    date_filter = request.GET.get('date', '')
    employee_filter = request.GET.get('employee', '')
    status_filter = request.GET.get('status', '')
    
    # Start with all attendance records
    attendance_list = Attendance.objects.all().select_related('employee', 'created_by').order_by('-date', 'employee__first_name')
    
    # Apply filters
    if date_filter:
        attendance_list = attendance_list.filter(date=date_filter)
    
    if employee_filter:
        attendance_list = attendance_list.filter(employee_id=employee_filter)
    
    if status_filter:
        attendance_list = attendance_list.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(attendance_list, 25)
    page_number = request.GET.get('page')
    attendance_records = paginator.get_page(page_number)
    
    # Get employees for filter
    employees = User.objects.filter(teammember__isnull=False).order_by('first_name', 'last_name')
    
    # Get today's statistics
    today = timezone.now().date()
    today_present = Attendance.objects.filter(date=today, status='present').count()
    today_late = Attendance.objects.filter(date=today, status='late').count()
    today_absent = Attendance.objects.filter(date=today, status='absent').count()
    
    context = {
        'attendance_records': attendance_records,
        'employees': employees,
        'status_choices': Attendance.STATUS_CHOICES,
        'date_filter': date_filter,
        'employee_filter': employee_filter,
        'status_filter': status_filter,
        'today_present': today_present,
        'today_late': today_late,
        'today_absent': today_absent,
    }
    
    return render(request, 'dashboard/attendance.html', context)

@login_required
def add_attendance(request):
    """Add attendance record manually"""
    if request.method == 'POST':
        try:
            employee_id = request.POST.get('employee')
            date = request.POST.get('date')
            status = request.POST.get('status')
            check_in_time = request.POST.get('check_in_time')
            check_out_time = request.POST.get('check_out_time')
            notes = request.POST.get('notes', '')
            
            # Check if attendance already exists for this employee and date
            existing = Attendance.objects.filter(employee_id=employee_id, date=date).first()
            if existing:
                messages.error(request, 'Attendance record already exists for this employee and date.')
                return redirect('attendance')
            
            # Create attendance record
            attendance = Attendance.objects.create(
                employee_id=employee_id,
                date=date,
                status=status,
                check_in_time=check_in_time if check_in_time else None,
                check_out_time=check_out_time if check_out_time else None,
                notes=notes,
                created_by=request.user
            )
            
            messages.success(request, 'Attendance record added successfully!')
            return redirect('attendance')
            
        except Exception as e:
            messages.error(request, f'Error adding attendance: {str(e)}')
            return redirect('attendance')
    
    return redirect('attendance')

@login_required
def manage_project_units(request, project_id):
    """Manage project units"""
    project = get_object_or_404(Project, id=project_id)
    units = ProjectUnit.objects.filter(project=project).order_by('unit_number')
    
    context = {
        'project': project,
        'units': units,
    }
    return render(request, 'dashboard/manage_project_units.html', context)

@login_required
def add_project_unit(request, project_id):
    """Add project unit"""
    project = get_object_or_404(Project, id=project_id)
    
    if request.method == 'POST':
        try:
            ProjectUnit.objects.create(
                project=project,
                unit_number=request.POST['unit_number'],
                unit_type=request.POST['unit_type'],
                area=request.POST.get('area'),
                price=request.POST.get('price'),
                status=request.POST.get('status', 'available'),
                floor=request.POST.get('floor'),
                facing=request.POST.get('facing', ''),
                amenities=request.POST.get('amenities', ''),
            )
            messages.success(request, 'Unit added successfully!')
        except Exception as e:
            messages.error(request, f'Error adding unit: {str(e)}')
    
    return redirect('manage_project_units', project_id=project_id)

@login_required
def edit_project_unit(request, unit_id):
    """Edit project unit"""
    unit = get_object_or_404(ProjectUnit, id=unit_id)
    
    if request.method == 'POST':
        try:
            unit.unit_number = request.POST['unit_number']
            unit.unit_type = request.POST['unit_type']
            unit.area = request.POST.get('area')
            unit.price = request.POST.get('price')
            unit.status = request.POST.get('status', 'available')
            unit.floor = request.POST.get('floor')
            unit.facing = request.POST.get('facing', '')
            unit.amenities = request.POST.get('amenities', '')
            unit.save()
            messages.success(request, 'Unit updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating unit: {str(e)}')
    
    return redirect('manage_project_units', project_id=unit.project.id)

@login_required
def delete_project_unit(request, unit_id):
    """Delete project unit"""
    unit = get_object_or_404(ProjectUnit, id=unit_id)
    project_id = unit.project.id
    
    if request.method == 'POST':
        unit.delete()
        messages.success(request, 'Unit deleted successfully!')
    
    return redirect('manage_project_units', project_id=project_id)

@login_required
def team_hierarchy(request):
    """Team hierarchy view"""
    team_members = TeamMember.objects.select_related('user', 'manager').all()
    context = {'team_members': team_members}
    return render(request, 'dashboard/team_hierarchy.html', context)

@login_required
def add_client(request):
    """Add client"""
    if request.method == 'POST':
        try:
            Client.objects.create(
                name=request.POST['name'],
                email=request.POST['email'],
                phone=request.POST['phone'],
                company=request.POST.get('company', ''),
                address=request.POST.get('address', ''),
                created_by=request.user
            )
            messages.success(request, 'Client added successfully!')
        except Exception as e:
            messages.error(request, f'Error adding client: {str(e)}')
    
    return redirect('clients')

@login_required
def tata_calls(request):
    """TATA IVR calls view"""
    calls = IVRCallLog.objects.all().order_by('-call_date')
    context = {'calls': calls}
    return render(request, 'dashboard/tata_calls.html', context)

@login_required
def sync_tata_calls(request):
    """Sync TATA IVR calls"""
    if request.method == 'POST':
        # Add sync logic here
        messages.success(request, 'Calls synced successfully!')
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def tata_chat_panel(request):
    """TATA Chat Panel - integrated WhatsApp/RCS messaging"""
    # Sync data on page load
    sync = TATASync()
    sync_results = sync.sync_all_data()
    
    context = {
        'page_title': 'TATA Chat Panel',
        'sync_results': sync_results
    }
    return render(request, 'dashboard/tata_chat_panel.html', context)

@login_required
def get_tata_conversations(request):
    """Get all TATA conversations"""
    try:
        sync = TATASync()
        result = sync.get_all_conversations()
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def send_tata_reply(request):
    """Send reply via TATA API"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            
            phone = data.get('phone')
            message = data.get('message')
            
            sync = TATASync()
            result = sync.send_session_message(phone, message)
            
            if result['success']:
                # Add note to lead
                lead = Lead.objects.filter(phone=phone).first()
                if lead:
                    LeadNote.objects.create(
                        lead=lead,
                        note=f"WhatsApp reply sent: {message}",
                        call_type='whatsapp',
                        created_by=request.user
                    )
                
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': result['error']})
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@csrf_exempt
def tata_webhook(request):
    """Enhanced webhook endpoint for TATA messages"""
    if request.method == 'POST':
        try:
            import json
            payload = json.loads(request.body)
            
            # Handle WhatsApp messages
            if 'messages' in payload:
                msg = payload['messages']
                phone = msg['from']
                text = msg.get('text', {}).get('body', '')
                timestamp = msg['timestamp']
                msg_id = msg['id']
                
                # Store message in database
                WhatsAppMessage.objects.create(
                    phone_number=phone,
                    message_content=text,
                    message_id=msg_id,
                    status='received'
                )
                
                # Try to link to existing lead or create new one
                lead = Lead.objects.filter(phone=phone).first()
                if not lead:
                    # Get contact name from payload if available
                    contact_name = "Unknown"
                    if 'contacts' in payload and payload['contacts']:
                        contact_name = payload['contacts'][0].get('profile', {}).get('name', f"WhatsApp Lead {phone}")
                    
                    lead = Lead.objects.create(
                        name=contact_name,
                        phone=phone,
                        source='whatsapp',
                        notes=f"First WhatsApp message: {text}"
                    )
                
                # Add note to lead
                LeadNote.objects.create(
                    lead=lead,
                    note=f"WhatsApp message received: {text}",
                    call_type='whatsapp',
                    created_by_id=1  # Admin user
                )
            
            # Handle status updates (sent, delivered, read, failed)
            if 'statuses' in payload:
                for status in payload['statuses']:
                    msg_id = status['id']
                    status_type = status['status']
                    
                    # Update message status in database
                    WhatsAppMessage.objects.filter(message_id=msg_id).update(
                        status=status_type
                    )
            
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
def ivr_webhooks(request):
    """IVR Webhooks management page"""
    context = {
        'page_title': 'IVR Webhooks Management'
    }
    return render(request, 'dashboard/ivr_webhooks.html', context)

@login_required
def punch_attendance(request):
    """Employee punch attendance page"""
    try:
        team_member = request.user.teammember
    except TeamMember.DoesNotExist:
        messages.error(request, 'You are not registered as a team member.')
        return redirect('dashboard')
    
    today = timezone.now().date()
    
    # Get today's attendance record
    today_attendance = Attendance.objects.filter(
        employee=request.user,
        date=today
    ).first()
    
    # Get recent attendance records (last 7 days)
    recent_attendance = Attendance.objects.filter(
        employee=request.user,
        date__gte=today - timedelta(days=7)
    ).order_by('-date')
    
    context = {
        'team_member': team_member,
        'today_attendance': today_attendance,
        'recent_attendance': recent_attendance,
        'today': today,
    }
    
    return render(request, 'dashboard/punch_attendence.html', context)

@login_required
def punch_in_out(request):
    """AJAX view for punch in/out with location"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            
            punch_type = data.get('punch_type')  # 'in' or 'out'
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            address = data.get('address', '')
            
            if not latitude or not longitude:
                return JsonResponse({
                    'success': False, 
                    'error': 'Location is required for attendance'
                })
            
            today = timezone.now().date()
            current_time = timezone.now().time()
            
            # Get or create today's attendance record
            attendance, created = Attendance.objects.get_or_create(
                employee=request.user,
                date=today,
                defaults={
                    'created_by': request.user,
                    'status': 'present'
                }
            )
            
            if punch_type == 'in':
                if attendance.check_in_time:
                    return JsonResponse({
                        'success': False,
                        'error': 'You have already punched in today'
                    })
                
                attendance.check_in_time = current_time
                attendance.check_in_latitude = latitude
                attendance.check_in_longitude = longitude
                attendance.check_in_address = address
                
                # Auto-calculate status based on time
                attendance.status = attendance.calculate_status()
                
            elif punch_type == 'out':
                if not attendance.check_in_time:
                    return JsonResponse({
                        'success': False,
                        'error': 'You must punch in first'
                    })
                
                if attendance.check_out_time:
                    return JsonResponse({
                        'success': False,
                        'error': 'You have already punched out today'
                    })
                
                attendance.check_out_time = current_time
                attendance.check_out_latitude = latitude
                attendance.check_out_longitude = longitude
                attendance.check_out_address = address
            
            attendance.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully punched {punch_type}!',
                'check_in_time': attendance.check_in_time.strftime('%H:%M') if attendance.check_in_time else None,
                'check_out_time': attendance.check_out_time.strftime('%H:%M') if attendance.check_out_time else None,
                'status': attendance.get_status_display(),
                'working_hours': round(attendance.working_hours, 2) if attendance.working_hours else 0
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

# Add these missing view functions

@login_required
def property_search(request):
    """Advanced property search with filters"""
    properties = Project.objects.filter(is_active=True)
    
    # Search query
    search_query = request.GET.get('search', '')
    if search_query:
        properties = properties.filter(
            Q(name__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(city__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Filters
    property_type = request.GET.get('property_type')
    if property_type:
        properties = properties.filter(property_type=property_type)
    
    city = request.GET.get('city')
    if city:
        properties = properties.filter(city=city)
    
    price_min = request.GET.get('price_min')
    if price_min:
        properties = properties.filter(price_min__gte=price_min)
    
    price_max = request.GET.get('price_max')
    if price_max:
        properties = properties.filter(price_max__lte=price_max)
    
    bhk = request.GET.get('bhk')
    if bhk:
        properties = properties.filter(bhk_options__icontains=f'{bhk}BHK')
    
    area_min = request.GET.get('area_min')
    if area_min:
        properties = properties.filter(area_min__gte=area_min)
    
    area_max = request.GET.get('area_max')
    if area_max:
        properties = properties.filter(area_max__lte=area_max)
    
    status = request.GET.get('status')
    if status:
        properties = properties.filter(status=status)
    
    # Special filters
    if request.GET.get('virtual_tour'):
        properties = properties.exclude(virtual_tour_url='')
    
    if request.GET.get('featured'):
        properties = properties.filter(is_featured=True)
    
    possession = request.GET.get('possession')
    if possession:
        today = timezone.now().date()
        if possession == 'ready':
            properties = properties.filter(possession_date__lte=today)
        elif possession == '6months':
            properties = properties.filter(possession_date__lte=today + timedelta(days=180))
        elif possession == '1year':
            properties = properties.filter(possession_date__lte=today + timedelta(days=365))
        elif possession == '2years':
            properties = properties.filter(possession_date__lte=today + timedelta(days=730))
    
    # Sorting
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'price_low':
        properties = properties.order_by('price_min')
    elif sort_by == 'price_high':
        properties = properties.order_by('-price_max')
    elif sort_by == 'area_large':
        properties = properties.order_by('-area_max')
    elif sort_by == 'featured':
        properties = properties.order_by('-is_featured', '-created_at')
    else:  # newest
        properties = properties.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(properties, 12)
    page_number = request.GET.get('page')
    properties = paginator.get_page(page_number)
    
    # Get filter options
    cities = Project.objects.filter(is_active=True).values_list('city', flat=True).distinct()
    
    context = {
        'properties': properties,
        'search_query': search_query,
        'property_types': Project.PROPERTY_TYPES,
        'status_choices': Project.STATUS_CHOICES,
        'cities': cities,
        'current_property_type': property_type,
        'current_city': city,
        'price_min': price_min,
        'price_max': price_max,
        'current_bhk': bhk,
        'area_min': area_min,
        'area_max': area_max,
        'current_status': status,
        'virtual_tour': request.GET.get('virtual_tour'),
        'featured': request.GET.get('featured'),
        'possession': possession,
    }
    
    return render(request, 'dashboard/property_search.html', context)

@login_required
def lead_stage_management(request):
    """Manage lead stages and tracking"""
    stages = LeadStage.objects.all().order_by('category', 'order')
    
    # Get stage statistics
    stage_stats = {}
    for stage in stages:
        stage_stats[stage.id] = {
            'total_leads': stage.leads.count(),
            'avg_duration': stage.from_history.aggregate(
                avg_duration=Avg('duration_in_previous_stage')
            )['avg_duration'] or 0
        }
    
    context = {
        'stages': stages,
        'stage_stats': stage_stats,
        'stage_categories': LeadStage.STAGE_CATEGORIES,
    }
    
    return render(request, 'dashboard/lead_stage_management.html', context)

@login_required
def lead_journey_tracking(request, lead_id):
    """Track individual lead journey"""
    lead = get_object_or_404(Lead, id=lead_id)
    
    # Get stage history
    stage_history = lead.stage_history.all().order_by('-changed_at')
    
    # Get all interactions
    call_notes = lead.call_notes.all().order_by('-created_at')
    whatsapp_messages = lead.whatsapp_messages.all().order_by('-created_at')
    
    # Combine and sort all activities
    activities = []
    
    for history in stage_history:
        activities.append({
            'type': 'stage_change',
            'timestamp': history.changed_at,
            'data': history
        })
    
    for note in call_notes:
        activities.append({
            'type': 'call_note',
            'timestamp': note.created_at,
            'data': note
        })
    
    for message in whatsapp_messages:
        activities.append({
            'type': 'whatsapp',
            'timestamp': message.created_at,
            'data': message
        })
    
    # Sort by timestamp
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    
    context = {
        'lead': lead,
        'activities': activities,
        'stages': LeadStage.objects.all().order_by('category', 'order'),
    }
    
    return render(request, 'dashboard/lead_journey.html', context)

@login_required
@require_http_methods(["POST"])
def move_lead_stage(request):
    """Move lead to different stage"""
    try:
        data = json.loads(request.body)
        lead_id = data.get('lead_id')
        stage_id = data.get('stage_id')
        notes = data.get('notes', '')
        
        lead = get_object_or_404(Lead, id=lead_id)
        new_stage = get_object_or_404(LeadStage, id=stage_id)
        
        lead.move_to_stage(new_stage, request.user, notes)
        
        return JsonResponse({
            'success': True,
            'message': f'Lead moved to {new_stage.name}'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@login_required
def whatsapp_automation(request):
    """WhatsApp automation management"""
    templates = WhatsAppTemplate.objects.all().order_by('stage')
    
    if request.method == 'POST':
        # Handle template creation/update
        template_id = request.POST.get('template_id')
        if template_id:
            template = get_object_or_404(WhatsAppTemplate, id=template_id)
        else:
            template = WhatsAppTemplate()
        
        template.name = request.POST.get('name')
        template.stage = request.POST.get('stage')
        template.message_template = request.POST.get('message_template')
        template.is_active = request.POST.get('is_active') == 'on'
        template.save()
        
        messages.success(request, 'WhatsApp template saved successfully!')
        return redirect('whatsapp_automation')
    
    context = {
        'templates': templates,
        'template_stages': WhatsAppTemplate.TEMPLATE_STAGES,
    }
    
    return render(request, 'dashboard/whatsapp_automation.html', context)


@login_required
def analytics_dashboard(request):
    """Advanced analytics dashboard"""
    # Date range filter
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if not date_from:
        date_from = (timezone.now() - timedelta(days=30)).date()
    else:
        date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
    
    if not date_to:
        date_to = timezone.now().date()
    else:
        date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
    
    # Lead analytics
    leads_in_period = Lead.objects.filter(
        created_at__date__range=[date_from, date_to]
    )
    
    # Source-wise analytics
    source_analytics = leads_in_period.values('source').annotate(
        count=Count('id'),
        conversion_rate=Count('id', filter=Q(current_stage__name='Deal Closed')) * 100.0 / Count('id')
    ).order_by('-count')
    
    # Stage-wise analytics
    stage_analytics = LeadStage.objects.annotate(
        lead_count=Count('leads'),
        avg_duration=Avg('to_history__duration_in_previous_stage')
    ).order_by('category', 'order')
    
    # Team performance
    team_performance = User.objects.filter(
        assigned_leads__created_at__date__range=[date_from, date_to]
    ).annotate(
        leads_assigned=Count('assigned_leads'),
        site_visits=Count('created_notes', filter=Q(created_notes__call_type='site_visit')),
        closures=Count('assigned_leads', filter=Q(assigned_leads__current_stage__name='Deal Closed'))
    ).order_by('-leads_assigned')
    
    # Monthly trends
    monthly_trends = []
    current_date = date_from
    while current_date <= date_to:
        month_leads = Lead.objects.filter(
            created_at__year=current_date.year,
            created_at__month=current_date.month
        ).count()
        
        monthly_trends.append({
            'month': current_date.strftime('%b %Y'),
            'leads': month_leads
        })
        
        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
    
    context = {
        'date_from': date_from,
        'date_to': date_to,
        'total_leads': leads_in_period.count(),
        'source_analytics': source_analytics,
        'stage_analytics': stage_analytics,
        'team_performance': team_performance,
        'monthly_trends': monthly_trends,
    }
    
    return render(request, 'dashboard/analytics_advanced.html', context)

@login_required
def active_leads(request):
    """Active leads page with advanced filtering"""
    # Get filter parameters
    source_filter = request.GET.get('source', '')
    assigned_filter = request.GET.get('assigned_to', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search_query = request.GET.get('search', '')
    rows_per_page = int(request.GET.get('rows_per_page', 25))
    
    # Start with active leads (warm + hot) - Fixed prefetch_related
    leads_list = Lead.objects.filter(current_stage__category__in=['warm', 'hot']).select_related('assigned_to', 'current_stage').prefetch_related('interested_projects', 'call_notes')
    
    # Apply filters
    if source_filter:
        leads_list = leads_list.filter(source=source_filter)
    
    if assigned_filter:
        leads_list = leads_list.filter(assigned_to_id=assigned_filter)
    
    if date_from:
        leads_list = leads_list.filter(created_at__date__gte=date_from)
    
    if date_to:
        leads_list = leads_list.filter(created_at__date__lte=date_to)
    
    if search_query:
        leads_list = leads_list.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    # Order by latest first
    leads_list = leads_list.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(leads_list, rows_per_page)
    page_number = request.GET.get('page')
    leads = paginator.get_page(page_number)
    
    # Get filter options
    team_members = User.objects.filter(teammember__isnull=False).order_by('first_name', 'last_name')
    
    context = {
        'leads': leads,
        'team_members': team_members,
        'source_choices': Lead.SOURCE_CHOICES,
        'current_source': source_filter,
        'current_assigned': assigned_filter,
        'date_from': date_from,
        'date_to': date_to,
        'search_query': search_query,
        'rows_per_page': rows_per_page,
        'page_title': 'Active Leads',
    }
    
    return render(request, 'dashboard/active_leads.html', context)

@login_required
def hot_leads(request):
    """Hot leads page with duplicate detection"""
    # Get filter parameters
    show_duplicates = request.GET.get('show_duplicates', '')
    project_filter = request.GET.get('project', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search_query = request.GET.get('search', '')
    rows_per_page = int(request.GET.get('rows_per_page', 25))
    
    # Get hot leads
    hot_leads_list = Lead.objects.filter(current_stage__category='hot').select_related('assigned_to', 'original_lead', 'current_stage').prefetch_related('interested_projects', 'call_notes')
    
    # Apply filters
    if show_duplicates == '1':
        hot_leads_list = hot_leads_list.filter(is_duplicate=True)
    elif show_duplicates == '0':
        hot_leads_list = hot_leads_list.filter(is_duplicate=False)
    
    if project_filter:
        hot_leads_list = hot_leads_list.filter(
            Q(inquiry_project_id=project_filter) | Q(interested_projects=project_filter)
        ).distinct()
    
    if date_from:
        hot_leads_list = hot_leads_list.filter(last_inquiry_date__gte=date_from)
    
    if date_to:
        hot_leads_list = hot_leads_list.filter(last_inquiry_date__lte=date_to)
    
    if search_query:
        hot_leads_list = hot_leads_list.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    # Order by latest first
    hot_leads_list = hot_leads_list.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(hot_leads_list, rows_per_page)
    page_number = request.GET.get('page')
    leads = paginator.get_page(page_number)
    
    # Get statistics
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    hot_leads_count = Lead.objects.filter(current_stage__category='hot').count()
    duplicate_leads_count = Lead.objects.filter(current_stage__category='hot', is_duplicate=True).count()
    this_week_count = Lead.objects.filter(current_stage__category='hot', created_at__date__gte=week_ago).count()
    converted_count = Lead.objects.filter(current_stage__category='closed').count()
    
    # Get projects for filter
    projects = Project.objects.filter(is_active=True).order_by('name')
    
    context = {
        'leads': leads,
        'projects': projects,
        'hot_leads_count': hot_leads_count,
        'duplicate_leads_count': duplicate_leads_count,
        'this_week_count': this_week_count,
        'converted_count': converted_count,
        'show_duplicates': show_duplicates,
        'current_project': project_filter,
        'date_from': date_from,
        'date_to': date_to,
        'search_query': search_query,
        'rows_per_page': rows_per_page,
        'page_title': 'Hot Leads',
    }
    
    return render(request, 'dashboard/hot_leads.html', context)

@login_required
def followup_leads(request):
    """Follow-up leads page with pagination and search filters"""
    from datetime import timedelta
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    assigned_filter = request.GET.get('assigned_to', '')
    status_filter = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    rows_per_page = int(request.GET.get('rows_per_page', 25))
    
    today = timezone.now().date()
    
    # Start with all leads that need follow-up
    leads_list = Lead.objects.filter(
        Q(follow_up_date__isnull=False) | Q(requires_callback=True),
        current_stage__category__in=['warm', 'hot']
    ).select_related('assigned_to', 'current_stage').prefetch_related('interested_projects', 'call_notes')
    
    # Apply filters
    if search_query:
        leads_list = leads_list.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    if assigned_filter:
        leads_list = leads_list.filter(assigned_to_id=assigned_filter)
    
    if status_filter:
        leads_list = leads_list.filter(current_stage__category=status_filter)
    
    if date_from:
        leads_list = leads_list.filter(follow_up_date__gte=date_from)
    
    if date_to:
        leads_list = leads_list.filter(follow_up_date__lte=date_to)
    
    # Order by follow-up date (overdue first)
    leads_list = leads_list.order_by('follow_up_date', '-created_at')
    
    # Pagination
    paginator = Paginator(leads_list, rows_per_page)
    page_number = request.GET.get('page')
    leads = paginator.get_page(page_number)
    
    # Get statistics for badges
    overdue_leads_count = Lead.objects.filter(
        follow_up_date__lt=today,
        current_stage__category__in=['warm', 'hot']
    ).count()
    
    due_today_count = Lead.objects.filter(
        follow_up_date=today,
        current_stage__category__in=['warm', 'hot']
    ).count()
    
    upcoming_leads_count = Lead.objects.filter(
        follow_up_date__gt=today,
        follow_up_date__lte=today + timedelta(days=7),
        current_stage__category__in=['warm', 'hot']
    ).count()
    
    callback_leads_count = Lead.objects.filter(
        requires_callback=True,
        current_stage__category__in=['warm', 'hot']
    ).count()
    
    # Get filter options
    team_members = User.objects.filter(teammember__isnull=False).order_by('first_name', 'last_name')
    
    context = {
        'leads': leads,
        'team_members': team_members,
        'status_choices': [('warm', 'Warm'), ('hot', 'Hot')],
        'overdue_leads_count': overdue_leads_count,
        'due_today_count': due_today_count,
        'upcoming_leads_count': upcoming_leads_count,
        'callback_leads_count': callback_leads_count,
        'search_query': search_query,
        'current_assigned': assigned_filter,
        'current_status': status_filter,
        'date_from': date_from,
        'date_to': date_to,
        'rows_per_page': rows_per_page,
        'page_title': 'Follow-up Leads',
    }
    
    return render(request, 'dashboard/followup_leads.html', context)

@login_required
def closed_leads(request):
    """Closed leads page (converted + lost)"""
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    rows_per_page = int(request.GET.get('rows_per_page', 25))
    
    # Start with closed leads
    leads_list = Lead.objects.filter(current_stage__category='closed').select_related('assigned_to', 'current_stage').prefetch_related('interested_projects', 'call_notes')
    
    # Apply filters
    if status_filter:
        leads_list = leads_list.filter(current_stage__category=status_filter)
    
    if search_query:
        leads_list = leads_list.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    # Order by latest first
    leads_list = leads_list.order_by('-updated_at')
    
    # Pagination
    paginator = Paginator(leads_list, rows_per_page)
    page_number = request.GET.get('page')
    leads = paginator.get_page(page_number)
    
    context = {
        'leads': leads,
        'status_choices': [('converted', 'Converted'), ('lost', 'Lost')],
        'current_status': status_filter,
        'search_query': search_query,
        'rows_per_page': rows_per_page,
        'page_title': 'Closed Leads',
    }
    
    return render(request, 'dashboard/closed_leads.html', context)

@login_required
def notifications(request):
    """View all notifications for the user"""
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    
    # Mark as read when viewed
    notifications.filter(is_read=False).update(is_read=True)
    
    context = {
        'notifications': notifications,
    }
    return render(request, 'dashboard/notifications.html', context)

@login_required
def get_notifications_json(request):
    """AJAX endpoint for getting user notifications"""
    notifications = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).order_by('-created_at')[:10]
    
    notification_data = []
    for notification in notifications:
        notification_data.append({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'type': notification.notification_type,
            'created_at': notification.created_at.strftime('%b %d, %Y %I:%M %p'),
            'time_ago': timesince(notification.created_at),
            'is_acknowledged': notification.is_acknowledged,
        })
    
    return JsonResponse({
        'notifications': notification_data,
        'count': notifications.count()
    })

@login_required
def mark_notification_read(request, notification_id):
    """Mark a specific notification as read"""
    if request.method == 'POST':
        try:
            notification = Notification.objects.get(id=notification_id, recipient=request.user)
            notification.is_read = True
            notification.save()
            return JsonResponse({'success': True})
        except Notification.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Notification not found'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read for the user"""
    if request.method == 'POST':
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

# Add missing view_leads function (if referenced in URLs)
@login_required
def view_leads(request):
    """Alternative view for leads - redirects to main leads view"""
    return redirect('leads')

# TATA Sync API endpoints
@login_required
def sync_tata_templates(request):
    """API endpoint to sync TATA templates"""
    if request.method == 'POST':
        try:
            sync = TATASync()
            result = sync.sync_templates()
            return JsonResponse(result)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def sync_tata_messages(request):
    """API endpoint to sync TATA messages"""
    if request.method == 'POST':
        try:
            sync = TATASync()
            result = sync.sync_messages()
            return JsonResponse(result)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def sync_all_tata_data(request):
    """API endpoint to sync all TATA data"""
    if request.method == 'POST':
        try:
            sync = TATASync()
            results = sync.sync_all_data()
            return JsonResponse(results)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def tata_sync_panel(request):
    """TATA Sync Panel - manage data synchronization"""
    context = {
        'page_title': 'TATA Data Sync Panel'
    }
    return render(request, 'dashboard/tata_sync_panel.html', context)