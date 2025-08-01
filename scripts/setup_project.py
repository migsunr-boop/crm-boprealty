import os
import sys
import django
from pathlib import Path

# Get the directory containing this script
script_dir = Path(__file__).resolve().parent
# Get the project root directory (parent of scripts)
project_root = script_dir.parent

# Add the project root to Python path
sys.path.insert(0, str(project_root))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'realty_dashboard.settings')

# Change to project directory
os.chdir(project_root)

# Setup Django
django.setup()

from django.core.management import execute_from_command_line

def setup_project():
    print("Setting up Django project...")
    
    # Create migrations
    print("Creating migrations...")
    execute_from_command_line(['manage.py', 'makemigrations'])
    
    # Apply migrations
    print("Applying migrations...")
    execute_from_command_line(['manage.py', 'migrate'])
    
    print("Project setup completed!")
    print("Now you can run: python scripts/create_sample_data.py")

if __name__ == "__main__":
    setup_project()
