# Custom migration to add database-level default for is_approved

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0005_fix_is_approved_default'),
    ]

    operations = [
        migrations.RunSQL(
            sql='ALTER TABLE authentication_companyuser ALTER COLUMN is_approved SET DEFAULT false;',
            reverse_sql='ALTER TABLE authentication_companyuser ALTER COLUMN is_approved DROP DEFAULT;',
        ),
    ]
