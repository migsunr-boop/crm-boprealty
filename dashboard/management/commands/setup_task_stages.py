from django.core.management.base import BaseCommand
from dashboard.models import TaskStage, TaskCategory

class Command(BaseCommand):
    help = 'Set up initial task stages and categories'

    def handle(self, *args, **options):
        # Create default task stages
        stages_data = [
            {'name': 'To Do', 'order': 1},
            {'name': 'In Progress', 'order': 2},
            {'name': 'Review', 'order': 3},
            {'name': 'Done', 'order': 4},
        ]
        
        for stage_data in stages_data:
            TaskStage.objects.get_or_create(
                name=stage_data['name'],
                defaults={'order': stage_data['order']}
            )
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(stages_data)} task stages'))
        
        # Create default task categories
        categories_data = [
            {'name': 'Project', 'color': '#3b82f6'},  # Blue
            {'name': 'Lead', 'color': '#10b981'},     # Green
            {'name': 'Meeting', 'color': '#8b5cf6'},  # Purple
            {'name': 'Follow-up', 'color': '#f59e0b'}, # Amber
            {'name': 'Admin', 'color': '#6b7280'},    # Gray
        ]
        
        for cat_data in categories_data:
            TaskCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={'color': cat_data['color']}
            )
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(categories_data)} task categories'))
