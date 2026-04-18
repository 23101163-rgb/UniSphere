from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_user_club_name_user_club_position_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='university_id',
            field=models.CharField(blank=True, max_length=20, unique=True),
        ),
    ]
