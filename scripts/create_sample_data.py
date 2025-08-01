import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'realty_dashboard.settings')
django.setup()

from django.contrib.auth.models import User
from dashboard.models import Project, Lead, TeamMember

def create_sample_data():
    print("Creating sample data...")
    
    # Create superuser if it doesn't exist
    if not User.objects.filter(username='admin').exists():
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@boprealty.com',
            password='admin123',
            first_name='Admin',
            last_name='User'
        )
        print(f'Created admin user: admin/admin123')
        
        # Create TeamMember for admin
        TeamMember.objects.create(
            user=admin_user,
            role='admin',
            phone='+91 9876543210',
            can_access_dashboard=True,
            can_access_projects=True,
            can_access_leads=True,
            can_access_reports=True,
            can_access_earnings=True,
            can_access_clients=True,
            can_access_calendar=True,
            can_access_tasks=True,
            can_access_analytics=True,
        )
        print('Created admin team member profile')
    else:
        print('Admin user already exists')

    # Create sample team members
    if not User.objects.filter(username='sales1').exists():
        sales_user = User.objects.create_user(
            username='sales1',
            email='sales1@boprealty.com',
            password='sales123',
            first_name='John',
            last_name='Sales'
        )
        
        TeamMember.objects.create(
            user=sales_user,
            role='sales_executive',
            phone='+91 9876543211',
            can_access_dashboard=True,
            can_access_projects=True,
            can_access_leads=True,
            can_access_clients=True,
            can_access_calendar=True,
            can_access_tasks=True,
        )
        print('Created sales user: sales1/sales123')

    # Create sample projects
    if not Project.objects.exists():
        projects_data = [
            {
                'name': 'Skyline Residency',
                'location': 'Bandra West, Mumbai',
                'description': 'Luxury apartments with modern amenities and stunning city views',
                'bhk_options': '2, 3, 4 BHK',
                'price_min': 25000000,
                'price_max': 42000000,
                'status': 'featured',
                'is_active': True
            },
            {
                'name': 'Green Valley Homes',
                'location': 'Whitefield, Bangalore',
                'description': 'Eco-friendly residential complex with green spaces',
                'bhk_options': '1, 2, 3 BHK',
                'price_min': 8500000,
                'price_max': 18000000,
                'status': 'upcoming',
                'is_active': True
            },
            {
                'name': 'Marina Heights',
                'location': 'Marine Drive, Mumbai',
                'description': 'Premium sea-facing apartments',
                'bhk_options': '3, 4, 5 BHK',
                'price_min': 52000000,
                'price_max': 85000000,
                'status': 'featured',
                'is_active': True
            },
            {
                'name': 'Tech Park Residences',
                'location': 'Gurgaon, Delhi NCR',
                'description': 'Modern living near IT hubs',
                'bhk_options': '2, 3 BHK',
                'price_min': 12000000,
                'price_max': 28000000,
                'status': 'active',
                'is_active': True
            }
        ]
        
        for project_data in projects_data:
            Project.objects.create(**project_data)
        
        print(f'Created {len(projects_data)} sample projects')

    # Create sample leads
    if not Lead.objects.exists():
        leads_data = [
            {
                'name': 'John Doe',
                'email': 'john@example.com',
                'phone': '+91 9876543210',
                'source': 'facebook',
                'status': 'hot',
                'notes': 'Interested in 3 BHK, budget 3-4 Cr',
                'budget_min': 30000000,
                'budget_max': 40000000
            },
            {
                'name': 'Jane Smith',
                'email': 'jane@example.com',
                'phone': '+91 9876543211',
                'source': 'google',
                'status': 'warm',
                'notes': 'Looking for 2 BHK, first-time buyer',
                'budget_min': 15000000,
                'budget_max': 25000000
            },
            {
                'name': 'Mike Johnson',
                'email': 'mike@example.com',
                'phone': '+91 9876543212',
                'source': 'website',
                'status': 'cold',
                'notes': 'Enquired about luxury apartments',
                'budget_min': 50000000,
                'budget_max': 80000000
            },
            {
                'name': 'Sarah Wilson',
                'email': 'sarah@example.com',
                'phone': '+91 9876543213',
                'source': 'referral',
                'status': 'warm',
                'notes': 'Referred by existing client',
                'budget_min': 20000000,
                'budget_max': 35000000
            },
            {
                'name': 'David Brown',
                'email': 'david@example.com',
                'phone': '+91 9876543214',
                'source': 'walk_in',
                'status': 'hot',
                'notes': 'Visited office, very interested',
                'budget_min': 40000000,
                'budget_max': 60000000
            }
        ]
        
        for lead_data in leads_data:
            Lead.objects.create(**lead_data)
        
        print(f'Created {len(leads_data)} sample leads')

    print('Sample data creation completed!')

if __name__ == '__main__':
    create_sample_data()
