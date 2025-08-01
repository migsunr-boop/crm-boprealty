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
import subprocess

def fix_migrations():
    print("Fixing Django migrations...")
    
    # Create dashboard app migrations directory if it doesn't exist
    migrations_dir = project_root / 'dashboard' / 'migrations'
    migrations_dir.mkdir(exist_ok=True)
    
    # Create __init__.py in migrations directory
    init_file = migrations_dir / '__init__.py'
    if not init_file.exists():
        init_file.touch()
        print("Created migrations/__init__.py")
    
    # Force create migrations for dashboard app
    print("Creating migrations for dashboard app...")
    try:
        execute_from_command_line(['manage.py', 'makemigrations', 'dashboard', '--verbosity=2'])
    except Exception as e:
        print(f"Error creating migrations: {e}")
        return False
    
    # Apply migrations
    print("Applying migrations...")
    try:
        execute_from_command_line(['manage.py', 'migrate', '--verbosity=2'])
    except Exception as e:
        print(f"Error applying migrations: {e}")
        return False
    
    print("Migrations fixed successfully!")
    return True

if __name__ == "__main__":
    if fix_migrations():
        print("Now you can run: python scripts/create_sample_data.py")
    else:
        print("Please check the error messages above and try again.")
