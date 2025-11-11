# Generated manually for bilingual support
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project_management', '0009_workflow_workflowtrigger_workflowexecution_and_more'),
    ]

    operations = [
        # Add bilingual fields to Project model
        migrations.AddField(
            model_name='project',
            name='name_en',
            field=models.CharField(blank=True, help_text='Project name in English', max_length=200, verbose_name='Project Name (English)'),
        ),
        migrations.AddField(
            model_name='project',
            name='name_zh',
            field=models.CharField(blank=True, help_text='Project name in Chinese', max_length=200, verbose_name='项目名称(中文)'),
        ),
        migrations.AddField(
            model_name='project',
            name='description_en',
            field=models.TextField(blank=True, help_text='Project description in English', verbose_name='Description (English)'),
        ),
        migrations.AddField(
            model_name='project',
            name='description_zh',
            field=models.TextField(blank=True, help_text='Project description in Chinese', verbose_name='描述(中文)'),
        ),
        migrations.AddField(
            model_name='project',
            name='primary_language',
            field=models.CharField(choices=[('en', 'English'), ('zh-hans', '简体中文')], default='en', help_text='Primary language for this project', max_length=10, verbose_name='Primary Language'),
        ),

        # Add bilingual fields to Task model
        migrations.AddField(
            model_name='task',
            name='title_en',
            field=models.CharField(blank=True, max_length=300, verbose_name='Task Title (English)'),
        ),
        migrations.AddField(
            model_name='task',
            name='title_zh',
            field=models.CharField(blank=True, max_length=300, verbose_name='任务标题(中文)'),
        ),
        migrations.AddField(
            model_name='task',
            name='description_en',
            field=models.TextField(blank=True, verbose_name='Description (English)'),
        ),
        migrations.AddField(
            model_name='task',
            name='description_zh',
            field=models.TextField(blank=True, verbose_name='描述(中文)'),
        ),
        migrations.AddField(
            model_name='task',
            name='primary_language',
            field=models.CharField(choices=[('en', 'English'), ('zh-hans', '简体中文')], default='en', max_length=10, verbose_name='Primary Language'),
        ),

        # Update indexes for Project
        migrations.AlterIndexTogether(
            name='project',
            index_together=set(),
        ),
        migrations.AddIndex(
            model_name='project',
            index=models.Index(fields=['status', 'priority'], name='project_man_status_a3a4ed_idx'),
        ),
        migrations.AddIndex(
            model_name='project',
            index=models.Index(fields=['owner', 'status'], name='project_man_owner_i_9c4d4e_idx'),
        ),
        migrations.AddIndex(
            model_name='project',
            index=models.Index(fields=['project_code'], name='project_man_project_5e8d4f_idx'),
        ),

        # Update indexes for Task
        migrations.AlterIndexTogether(
            name='task',
            index_together=set(),
        ),
        migrations.AddIndex(
            model_name='task',
            index=models.Index(fields=['project', 'status'], name='project_man_project_7a8c3d_idx'),
        ),
        migrations.AddIndex(
            model_name='task',
            index=models.Index(fields=['project', 'kanban_column'], name='project_man_project_1b2c5f_idx'),
        ),
        migrations.AddIndex(
            model_name='task',
            index=models.Index(fields=['status', 'due_date'], name='project_man_status_2d3c6e_idx'),
        ),
        migrations.AddIndex(
            model_name='task',
            index=models.Index(fields=['project', 'priority'], name='project_man_project_4e5d8f_idx'),
        ),
    ]
