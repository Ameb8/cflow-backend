# Generated by Django 5.2 on 2025-06-07 01:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_file_file_content'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='folder',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='folder',
            name='parent',
        ),
        migrations.RemoveField(
            model_name='folder',
            name='user',
        ),
        migrations.DeleteModel(
            name='File',
        ),
        migrations.DeleteModel(
            name='Folder',
        ),
    ]
