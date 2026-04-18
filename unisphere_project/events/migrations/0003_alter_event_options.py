from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0002_event_organizer_category'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='event',
            options={'ordering': ['date', 'time', '-created_at']},
        ),
    ]