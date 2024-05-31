# Generated by Django 4.2.7 on 2024-05-29 14:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('telegrambot', '0003_stage_assigned_worker'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='stage',
            name='assigned_worker',
        ),
        migrations.AddField(
            model_name='stage',
            name='workers_assigned',
            field=models.ManyToManyField(blank=True, related_name='assigned_stages', to='telegrambot.telegramuser'),
        ),
    ]