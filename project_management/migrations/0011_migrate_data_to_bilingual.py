# Data migration to copy existing data to bilingual fields
from django.db import migrations


def migrate_project_data(apps, schema_editor):
    """Copy existing Project data to English fields"""
    Project = apps.get_model('project_management', 'Project')

    for project in Project.objects.all():
        # Copy name to name_en (assuming existing data is English)
        if hasattr(project, 'name') and project.name:
            project.name_en = project.name
            # Also copy to name_zh as placeholder
            project.name_zh = project.name

        # Copy description to description_en
        if hasattr(project, 'description') and project.description:
            project.description_en = project.description
            # Also copy to description_zh as placeholder
            project.description_zh = project.description

        project.save(update_fields=['name_en', 'name_zh', 'description_en', 'description_zh'])


def migrate_task_data(apps, schema_editor):
    """Copy existing Task data to English fields"""
    Task = apps.get_model('project_management', 'Task')

    for task in Task.objects.all():
        # Copy title to title_en (assuming existing data is English)
        if hasattr(task, 'title') and task.title:
            task.title_en = task.title
            # Also copy to title_zh as placeholder
            task.title_zh = task.title

        # Copy description to description_en
        if hasattr(task, 'description') and task.description:
            task.description_en = task.description
            # Also copy to description_zh as placeholder
            task.description_zh = task.description

        task.save(update_fields=['title_en', 'title_zh', 'description_en', 'description_zh'])


def reverse_migration(apps, schema_editor):
    """Reverse migration - copy data back from bilingual fields"""
    Project = apps.get_model('project_management', 'Project')
    Task = apps.get_model('project_management', 'Task')

    # Copy back from name_en to name
    for project in Project.objects.all():
        if project.name_en:
            project.name = project.name_en
        if project.description_en:
            project.description = project.description_en
        project.save(update_fields=['name', 'description'])

    # Copy back from title_en to title
    for task in Task.objects.all():
        if task.title_en:
            task.title = task.title_en
        if task.description_en:
            task.description = task.description_en
        task.save(update_fields=['title', 'description'])


class Migration(migrations.Migration):

    dependencies = [
        ('project_management', '0010_add_bilingual_fields'),
    ]

    operations = [
        migrations.RunPython(migrate_project_data, reverse_migration),
        migrations.RunPython(migrate_task_data, reverse_migration),
    ]
