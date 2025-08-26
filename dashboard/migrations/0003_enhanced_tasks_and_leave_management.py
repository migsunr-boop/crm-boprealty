# Generated migration for enhanced task hierarchy and leave management

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dashboard', '0002_add_task_fields'),
    ]

    operations = [
        # Add hierarchy fields to Task model
        migrations.AddField(
            model_name='task',
            name='parent_task',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='subtasks', to='dashboard.task'),
        ),
        migrations.AddField(
            model_name='task',
            name='order',
            field=models.PositiveIntegerField(default=0, help_text='Order within parent or stage'),
        ),
        
        # Create LeaveType model
        migrations.CreateModel(
            name='LeaveType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('days_allowed_per_year', models.PositiveIntegerField(default=0)),
                ('carry_forward_allowed', models.BooleanField(default=False)),
                ('max_carry_forward_days', models.PositiveIntegerField(default=0)),
                ('requires_approval', models.BooleanField(default=True)),
                ('color', models.CharField(default='#f59e0b', max_length=7)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        
        # Create LeaveApplication model
        migrations.CreateModel(
            name='LeaveApplication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('from_date', models.DateField()),
                ('to_date', models.DateField()),
                ('days_requested', models.PositiveIntegerField()),
                ('reason', models.TextField()),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('rejection_reason', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('approved_at', models.DateTimeField(blank=True, null=True)),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_leaves', to=settings.AUTH_USER_MODEL)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='leave_applications', to=settings.AUTH_USER_MODEL)),
                ('leave_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dashboard.leavetype')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        
        # Create CompOffRequest model
        migrations.CreateModel(
            name='CompOffRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('worked_date', models.DateField(help_text='Date when extra work was done')),
                ('requested_date', models.DateField(help_text='Date when comp-off is requested')),
                ('reason', models.TextField(help_text='Reason for working on holiday/weekend')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('approved_at', models.DateTimeField(blank=True, null=True)),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_compoffs', to=settings.AUTH_USER_MODEL)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='compoff_requests', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        
        # Update Attendance model with new fields
        migrations.AddField(
            model_name='attendance',
            name='leave_application',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='dashboard.leaveapplication'),
        ),
        migrations.AddField(
            model_name='attendance',
            name='compoff_request',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='dashboard.compoffrequest'),
        ),
        
        # Update attendance status choices to include comp_off
        migrations.AlterField(
            model_name='attendance',
            name='status',
            field=models.CharField(choices=[('present', 'Present'), ('absent', 'Absent'), ('late', 'Late'), ('half_day', 'Half Day'), ('work_from_home', 'Work From Home'), ('on_leave', 'On Leave'), ('comp_off', 'Comp Off')], default='present', max_length=20),
        ),
        
        # Update Task model ordering
        migrations.AlterModelOptions(
            name='task',
            options={'ordering': ['order', '-created_at']},
        ),
        
        # Create default leave types
        migrations.RunSQL(
            "INSERT INTO dashboard_leavetype (name, days_allowed_per_year, carry_forward_allowed, max_carry_forward_days, requires_approval, color) VALUES "
            "('Annual Leave', 12, true, 5, true, '#3b82f6'), "
            "('Sick Leave', 8, false, 0, false, '#ef4444'), "
            "('Casual Leave', 6, false, 0, true, '#10b981'), "
            "('Maternity Leave', 90, false, 0, true, '#f59e0b'), "
            "('Paternity Leave', 15, false, 0, true, '#8b5cf6');",
            reverse_sql="DELETE FROM dashboard_leavetype WHERE name IN ('Annual Leave', 'Sick Leave', 'Casual Leave', 'Maternity Leave', 'Paternity Leave');"
        ),
    ]