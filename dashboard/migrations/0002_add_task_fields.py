# Generated migration for new task fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='due_time',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='task',
            name='event_date',
            field=models.DateTimeField(blank=True, help_text='Event or meeting date/time', null=True),
        ),
        migrations.AddField(
            model_name='task',
            name='location',
            field=models.TextField(blank=True, help_text='Full address or location details'),
        ),
        migrations.AddField(
            model_name='task',
            name='venue',
            field=models.CharField(blank=True, help_text='Meeting venue or event location', max_length=255),
        ),
    ]