from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from dashboard.models import (
    Project, Lead, TeamMember, CalendarEvent, Task, TaskStage, 
    TaskCategory, Notification, Attendance, LeadNote
)
from datetime import datetime, timedelta, date
import random

class Command(BaseCommand):
    help = 'Populate the database with sample data for testing'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Creating sample data for Django Realty Dashboard...'))
        
        # Create admin user if not exists
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@realty.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("✅ Admin user created (username: admin, password: admin123)"))
        
        # Create team members with birthdays
        team_data = [
            {
                'username': 'john_manager',
                'first_name': 'John',
                'last_name': 'Smith',
                'email': 'john@realty.com',
                'role': 'manager',
                'phone': '+91-9876543210',
                'birthday': date(1985, 12, 25),  # Christmas birthday
                'joining_date': date(2020, 1, 15),
            },
            {
                'username': 'sarah_sales',
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'email': 'sarah@realty.com',
                'role': 'sales_executive',
                'phone': '+91-9876543211',
                'birthday': date(1990, 3, 15),
                'joining_date': date(2021, 6, 1),
            },
            {
                'username': 'mike_senior',
                'first_name': 'Mike',
                'last_name': 'Wilson',
                'email': 'mike@realty.com',
                'role': 'senior_sales_executive',
                'phone': '+91-9876543212',
                'birthday': date(1988, 7, 20),
                'joining_date': date(2019, 3, 10),
            },
            {
                'username': 'lisa_marketing',
                'first_name': 'Lisa',
                'last_name': 'Brown',
                'email': 'lisa@realty.com',
                'role': 'marketing_executive',
                'phone': '+91-9876543213',
                'birthday': date.today() + timedelta(days=1),  # Tomorrow's birthday!
                'joining_date': date(2022, 8, 5),
            },
            {
                'username': 'david_lead',
                'first_name': 'David',
                'last_name': 'Garcia',
                'email': 'david@realty.com',
                'role': 'team_lead',
                'phone': '+91-9876543214',
                'birthday': date.today(),  # Today's birthday!
                'joining_date': date(2018, 11, 20),
            }
        ]
        
        created_users = []
        for data in team_data:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': data['email'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                
                # Create team member profile
                TeamMember.objects.get_or_create(
                    user=user,
                    defaults={
                        'role': data['role'],
                        'phone': data['phone'],
                        'date_of_birth': data['birthday'],
                        'joining_date': data['joining_date'],
                        'can_access_dashboard': True,
                        'can_access_projects': True,
                        'can_access_leads': True,
                        'can_access_calendar': True,
                        'can_access_tasks': True,
                    }
                )
                created_users.append(user)
        
        self.stdout.write(self.style.SUCCESS(f"✅ Created {len(created_users)} team members"))
        
        # Create sample projects
        projects_data = [
            {
                'name': 'Skyline Towers',
                'location': 'Bandra West, Mumbai',
                'description': 'Luxury residential towers with sea view',
                'bhk_options': '2BHK, 3BHK, 4BHK',
                'price_min': 15000000,
                'price_max': 35000000,
                'status': 'featured',
                'total_units': 200,
                'available_units': 45,
                'amenities': 'Swimming Pool, Gym, Club House, Garden, Security',
                'features': 'Sea View, Premium Finishes, Smart Home, Parking',
                'developer_name': 'Skyline Developers',
            },
            {
                'name': 'Green Valley Homes',
                'location': 'Whitefield, Bangalore',
                'description': 'Eco-friendly residential community',
                'bhk_options': '1BHK, 2BHK, 3BHK',
                'price_min': 4500000,
                'price_max': 12000000,
                'status': 'construction',
                'total_units': 150,
                'available_units': 89,
                'amenities': 'Park, Playground, Solar Power, Rainwater Harvesting',
                'features': 'Green Building, Energy Efficient, Natural Lighting',
                'developer_name': 'Green Homes Ltd',
            },
            {
                'name': 'Metro Heights',
                'location': 'Gurgaon Sector 45',
                'description': 'Modern apartments near metro station',
                'bhk_options': '2BHK, 3BHK',
                'price_min': 8000000,
                'price_max': 18000000,
                'status': 'planning',
                'total_units': 120,
                'available_units': 120,
                'amenities': 'Metro Connectivity, Shopping Mall, Food Court',
                'features': 'Modern Design, High Speed Elevators, CCTV',
                'developer_name': 'Metro Builders',
            }
        ]
        
        created_projects = []
        for data in projects_data:
            project, created = Project.objects.get_or_create(
                name=data['name'],
                defaults={
                    **data,
                    'created_by': admin_user,
                    'possession_date': date.today() + timedelta(days=random.randint(180, 720))
                }
            )
            if created:
                created_projects.append(project)
        
        self.stdout.write(self.style.SUCCESS(f"✅ Created {len(created_projects)} projects"))
        
        # Create sample leads
        leads_data = [
            {
                'name': 'Rajesh Kumar',
                'email': 'rajesh.kumar@email.com',
                'phone': '+91-9123456789',
                'source': 'website',
                'status': 'hot',
                'budget_min': 15000000,
                'budget_max': 25000000,
                'notes': 'Interested in sea view apartments. Looking for 3BHK.',
            },
            {
                'name': 'Priya Sharma',
                'email': 'priya.sharma@email.com',
                'phone': '+91-9123456790',
                'source': 'referral',
                'status': 'warm',
                'budget_min': 8000000,
                'budget_max': 15000000,
                'notes': 'First time buyer. Needs financing assistance.',
            },
            {
                'name': 'Amit Patel',
                'email': 'amit.patel@email.com',
                'phone': '+91-9123456791',
                'source': 'social_media',
                'status': 'hot',
                'budget_min': 5000000,
                'budget_max': 10000000,
                'notes': 'Looking for investment property in Bangalore.',
            },
            {
                'name': 'Sneha Reddy',
                'email': 'sneha.reddy@email.com',
                'phone': '+91-9123456792',
                'source': 'advertisement',
                'status': 'warm',
                'budget_min': 12000000,
                'budget_max': 20000000,
                'notes': 'Wants modern amenities and good connectivity.',
            },
            {
                'name': 'Vikram Singh',
                'email': 'vikram.singh@email.com',
                'phone': '+91-9123456793',
                'source': 'walk_in',
                'status': 'converted',
                'budget_min': 18000000,
                'budget_max': 25000000,
                'notes': 'Purchased 3BHK in Skyline Towers. Happy customer.',
            },
            {
                'name': 'Anita Gupta',
                'email': 'anita.gupta@email.com',
                'phone': '+91-9123456794',
                'source': 'phone_call',
                'status': 'cold',
                'budget_min': 6000000,
                'budget_max': 12000000,
                'notes': 'Not ready to buy immediately. Follow up in 6 months.',
            }
        ]
        
        created_leads = []
        all_users = list(User.objects.filter(teammember__isnull=False))
        
        for i, data in enumerate(leads_data):
            lead, created = Lead.objects.get_or_create(
                email=data['email'],
                defaults={
                    **data,
                    'assigned_to': random.choice(all_users) if all_users else None,
                    'last_contact_date': date.today() - timedelta(days=random.randint(1, 30)),
                    'follow_up_date': date.today() + timedelta(days=random.randint(1, 14)) if data['status'] in ['warm', 'hot'] else None,
                    'requires_callback': random.choice([True, False]) if data['status'] in ['warm', 'hot'] else False,
                }
            )
            if created:
                # Assign random projects
                if created_projects:
                    lead.interested_projects.add(random.choice(created_projects))
                    if random.choice([True, False]):  # 50% chance of second project
                        lead.interested_projects.add(random.choice(created_projects))
                created_leads.append(lead)
        
        self.stdout.write(self.style.SUCCESS(f"✅ Created {len(created_leads)} leads"))
        
        # Create birthday notifications for today's birthdays
        today = date.today()
        birthday_members = TeamMember.objects.filter(date_of_birth__day=today.day, date_of_birth__month=today.month)
        
        for member in birthday_members:
            for user in User.objects.filter(is_active=True):
                Notification.objects.get_or_create(
                    recipient=user,
                    title="🎂 Birthday Today!",
                    message=f"Today is {member.user.get_full_name()}'s birthday! Don't forget to wish them!",
                    notification_type='birthday',
                    related_object_id=member.id,
                    related_object_type='teammember',
                    defaults={'created_at': datetime.now()}
                )
        
        self.stdout.write(self.style.SUCCESS("✅ Created birthday notifications"))
        
        self.stdout.write(self.style.SUCCESS("\n🎉 Sample data creation completed!"))
        self.stdout.write(self.style.SUCCESS("\n📋 Summary:"))
        self.stdout.write(self.style.SUCCESS(f"   👥 Users: {User.objects.count()}"))
        self.stdout.write(self.style.SUCCESS(f"   🏢 Projects: {Project.objects.count()}"))
        self.stdout.write(self.style.SUCCESS(f"   📞 Leads: {Lead.objects.count()}"))
        self.stdout.write(self.style.SUCCESS(f"   🔔 Notifications: {Notification.objects.count()}"))
        
        self.stdout.write(self.style.SUCCESS("\n🔑 Login Credentials:"))
        self.stdout.write(self.style.SUCCESS("   Admin: username=admin, password=admin123"))
        self.stdout.write(self.style.SUCCESS("   Team Members: password=password123"))
        self.stdout.write(self.style.SUCCESS("   - john_manager, sarah_sales, mike_senior, lisa_marketing, david_lead"))
        
        self.stdout.write(self.style.SUCCESS("\n🎂 Birthday Notifications:"))
        self.stdout.write(self.style.SUCCESS("   - David Garcia has birthday TODAY!"))
        self.stdout.write(self.style.SUCCESS("   - Lisa Brown has birthday TOMORROW!"))
        self.stdout.write(self.style.SUCCESS("   - Check notifications page to see birthday alerts"))
