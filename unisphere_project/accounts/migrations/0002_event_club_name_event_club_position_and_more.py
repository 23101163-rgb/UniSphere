from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='club_name',
            field=models.CharField(blank=True, choices=[('', 'Select Club'), ('uap_programming_contest_club', 'UAP Programming Contest Club'), ('software_hardware_club', 'Software and Hardware Club'), ('cyber_security_club', 'Cyber Security Club, CSE, UAP'), ('career_development_club', 'Career Development Club'), ('math_club', 'Math Club'), ('research_publication_units', 'Research and Publication Units'), ('robotics_club', 'Robotics Club'), ('photography_club', 'Photography Club'), ('sports_club', 'Sports Club'), ('cultural_club', 'Cultural Club')], max_length=100),
        ),
        migrations.AddField(
            model_name='user',
            name='club_position',
            field=models.CharField(blank=True, choices=[('', 'Select Position'), ('member', 'Member'), ('executive_member', 'Executive Member'), ('senior_executive', 'Senior Executive'), ('assistant_secretary', 'Assistant Secretary'), ('secretary', 'Secretary'), ('vice_president', 'Vice President'), ('president', 'President'), ('coordinator', 'Coordinator'), ('organizer', 'Organizer'), ('volunteer', 'Volunteer'), ('other', 'Other')], max_length=50),
        ),
        migrations.AddField(
            model_name='user',
            name='is_club_member',
            field=models.BooleanField(default=False),
        ),
    ]