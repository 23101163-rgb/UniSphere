from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0005_event_club_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='club_name',
            field=models.CharField(blank=True, choices=[('uap_programming_contest_club', 'UAP Programming Contest Club'), ('software_hardware_club', 'Software and Hardware Club'), ('cyber_security_club', 'Cyber Security Club, CSE, UAP'), ('career_development_club', 'Career Development Club'), ('math_club', 'Math Club'), ('research_publication_units', 'Research and Publication Units'), ('robotics_club', 'Robotics Club'), ('photography_club', 'Photography Club'), ('sports_club', 'Sports Club'), ('cultural_club', 'Cultural Club')], max_length=50),
        ),
    ]