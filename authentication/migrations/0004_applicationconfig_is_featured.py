# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0003_companyuser_approved_at_companyuser_approved_by_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='applicationconfig',
            name='is_featured',
            field=models.BooleanField(default=False, help_text='Whether this application is featured on the dashboard', verbose_name='Is Featured'),
        ),
    ]
