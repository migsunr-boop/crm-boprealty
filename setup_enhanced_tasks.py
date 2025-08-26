#!/usr/bin/env python
"""
Setup script for enhanced task management system
Run this after creating the migration to set up default task stages and categories
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'realty_dashboard.settings')
django.setup()

from dashboard.models import TaskStage, TaskCategory, LeaveType

def setup_task_stages():
    """Create default task stages if they don't exist"""
    stages = [
        {'name': 'To Do', 'order': 1, 'color': '#6b7280'},
        {'name': 'In Progress', 'order': 2, 'color': '#3b82f6'},
        {'name': 'Review', 'order': 3, 'color': '#f59e0b'},
        {'name': 'Done', 'order': 4, 'color': '#10b981'},
    ]
    
    for stage_data in stages:
        stage, created = TaskStage.objects.get_or_create(
            name=stage_data['name'],
            defaults={
                'order': stage_data['order'],
                'color': stage_data['color']
            }
        )
        if created:
            print(f"✅ Created task stage: {stage.name}")
        else:
            print(f"ℹ️  Task stage already exists: {stage.name}")

def setup_task_categories():
    """Create default task categories if they don't exist"""
    categories = [
        {'name': 'Lead Follow-up', 'color': '#3b82f6', 'description': 'Tasks related to following up with leads'},
        {'name': 'Site Visit', 'color': '#10b981', 'description': 'Site visit scheduling and coordination'},
        {'name': 'Documentation', 'color': '#f59e0b', 'description': 'Document preparation and processing'},
        {'name': 'Meeting', 'color': '#8b5cf6', 'description': 'Internal and client meetings'},
        {'name': 'Marketing', 'color': '#ef4444', 'description': 'Marketing and promotional activities'},
        {'name': 'Administrative', 'color': '#6b7280', 'description': 'Administrative and operational tasks'},
    ]
    
    for category_data in categories:
        category, created = TaskCategory.objects.get_or_create(
            name=category_data['name'],
            defaults={
                'color': category_data['color'],
                'description': category_data['description']
            }
        )
        if created:
            print(f"✅ Created task category: {category.name}")
        else:
            print(f"ℹ️  Task category already exists: {category.name}")

def setup_leave_types():
    """Create default leave types if they don't exist"""
    leave_types = [
        {
            'name': 'Annual Leave',
            'days_allowed_per_year': 12,
            'carry_forward_allowed': True,
            'max_carry_forward_days': 5,
            'requires_approval': True,
            'color': '#3b82f6'
        },
        {
            'name': 'Sick Leave',
            'days_allowed_per_year': 8,
            'carry_forward_allowed': False,
            'max_carry_forward_days': 0,
            'requires_approval': False,
            'color': '#ef4444'
        },
        {
            'name': 'Casual Leave',
            'days_allowed_per_year': 6,
            'carry_forward_allowed': False,
            'max_carry_forward_days': 0,
            'requires_approval': True,
            'color': '#10b981'
        },
        {
            'name': 'Maternity Leave',
            'days_allowed_per_year': 90,
            'carry_forward_allowed': False,
            'max_carry_forward_days': 0,
            'requires_approval': True,
            'color': '#f59e0b'
        },
        {
            'name': 'Paternity Leave',
            'days_allowed_per_year': 15,
            'carry_forward_allowed': False,
            'max_carry_forward_days': 0,
            'requires_approval': True,
            'color': '#8b5cf6'
        },
    ]
    
    for leave_data in leave_types:
        leave_type, created = LeaveType.objects.get_or_create(
            name=leave_data['name'],
            defaults=leave_data
        )
        if created:
            print(f"✅ Created leave type: {leave_type.name}")
        else:
            print(f"ℹ️  Leave type already exists: {leave_type.name}")

def main():
    print("🚀 Setting up enhanced task management system...")
    print()
    
    print("📋 Setting up task stages...")
    setup_task_stages()
    print()
    
    print("🏷️  Setting up task categories...")
    setup_task_categories()
    print()
    
    print("🏖️  Setting up leave types...")
    setup_leave_types()
    print()
    
    print("✅ Enhanced task management system setup complete!")
    print()
    print("📝 Next steps:")
    print("1. Run: python manage.py makemigrations")
    print("2. Run: python manage.py migrate")
    print("3. Access enhanced tasks at: /tasks/?enhanced=true")
    print("4. Check profile page for updated attendance tracking")

if __name__ == '__main__':
    main()