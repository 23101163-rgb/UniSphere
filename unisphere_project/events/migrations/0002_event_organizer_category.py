from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='organizer_category',
            field=models.CharField(choices=[('club', 'Club Event'), ('non_club', 'Non-Club Event')], default='club', max_length=20),
        ),
    ]