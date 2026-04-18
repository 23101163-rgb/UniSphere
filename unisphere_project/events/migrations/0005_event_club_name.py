from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0004_alter_eventregistration_options_remove_event_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='club_name',
            field=models.CharField(blank=True, choices=[('robotics_club', 'Robotics Club'), ('programming_club', 'Programming Club'), ('career_club', 'Career Club'), ('english_club', 'English Club'), ('cultural_club', 'Cultural Club'), ('sports_club', 'Sports Club'), ('other', 'Other Club')], max_length=50),
        ),
    ]