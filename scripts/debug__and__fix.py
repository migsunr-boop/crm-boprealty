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
from django.conf import settings
import sqlite3

def debug_and_fix():
    print("=== Django Project Debug and Fix ===")
    
    # Check if dashboard app is in INSTALLED_APPS
    print(f"INSTALLED_APPS: {settings.INSTALLED_APPS}")
    if 'dashboard' not in settings.INSTALLED_APPS:
        print("❌ ERROR: 'dashboard' app is not in INSTALLED_APPS!")
        return False
    else:
        print("✅ Dashboard app is properly installed")
    
    # Check if models.py exists
    models_file = project_root / 'dashboard' / 'models.py'
    if not models_file.exists():
        print("❌ ERROR: dashboard/models.py does not exist!")
        return False
    else:
        print("✅ Models file exists")
    
    # Check migrations directory
    migrations_dir = project_root / 'dashboard' / 'migrations'
    if not migrations_dir.exists():
        print("📁 Creating migrations directory...")
        migrations_dir.mkdir(exist_ok=True)
    
    # Create __init__.py in migrations
    init_file = migrations_dir / '__init__.py'
    if not init_file.exists():
        print("📄 Creating migrations/__init__.py...")
        init_file.touch()
    
    # Remove existing database to start fresh
    db_file = project_root / 'db.sqlite3'
    if db_file.exists():
        print("🗑️ Removing existing database...")
        db_file.unlink()
    
    # Remove existing migration files (except __init__.py)
    for migration_file in migrations_dir.glob('*.py'):
        if migration_file.name != '__init__.py':
            print(f"🗑️ Removing old migration: {migration_file.name}")
            migration_file.unlink()
    
    # Create fresh migrations
    print("📝 Creating fresh migrations...")
    try:
        execute_from_command_line(['manage.py', 'makemigrations', 'dashboard', '--verbosity=2'])
        print("✅ Migrations created successfully")
    except Exception as e:
        print(f"❌ Error creating migrations: {e}")
        return False
    
    # Apply migrations
    print("🔄 Applying migrations...")
    try:
        execute_from_command_line(['manage.py', 'migrate', '--verbosity=2'])
        print("✅ Migrations applied successfully")
    except Exception as e:
        print(f"❌ Error applying migrations: {e}")
        return False
    
    # Verify tables were created
    print("🔍 Verifying database tables...")
    try:
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()
        
        table_names = [table[0] for table in tables]
        print(f"📊 Created tables: {table_names}")
        
        required_tables = [
            'dashboard_project',
            'dashboard_lead', 
            'dashboard_client',
            'dashboard_earning',
            'dashboard_task',
            'dashboard_meeting',
            'dashboard_analytics'
        ]
        
        missing_tables = [table for table in required_tables if table not in table_names]
        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
            return False
        else:
            print("✅ All required tables created successfully")
            
    except Exception as e:
        print(f"❌ Error verifying tables: {e}")
        return False
    
    print("\n🎉 Database setup completed successfully!")
    print("Now you can run: python scripts/create_sample_data.py")
    return True

if __name__ == "__main__":
    debug_and_fix()
