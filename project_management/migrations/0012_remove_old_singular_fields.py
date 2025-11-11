# Remove old singular language fields after migrating to bilingual fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('project_management', '0011_migrate_data_to_bilingual'),
    ]

    operations = [
        # Remove old Project fields
        migrations.RemoveField(
            model_name='project',
            name='name',
        ),
        migrations.RemoveField(
            model_name='project',
            name='description',
        ),

        # Remove old Task fields
        migrations.RemoveField(
            model_name='task',
            name='title',
        ),
        migrations.RemoveField(
            model_name='task',
            name='description',
        ),
    ]
