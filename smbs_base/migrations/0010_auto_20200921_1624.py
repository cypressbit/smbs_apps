# Generated by Django 3.1.1 on 2020-09-21 16:24

from django.db import migrations, models
import smbs_apps.smbs_base.models
import smbs_apps.smbs_base.storage


class Migration(migrations.Migration):

    dependencies = [
        ('smbs_base', '0009_basesettings_bootstrap_theme'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='basesettings',
            name='bootstrap_theme',
        ),
        migrations.AddField(
            model_name='basesettings',
            name='navbar_type',
            field=models.CharField(blank=True, choices=[('navbar_dark', 'Dark'), ('navbar_light', 'Light')], max_length=64, null=True),
        ),
        migrations.AddField(
            model_name='basesettings',
            name='theme',
            field=models.FileField(blank=True, null=True, storage=smbs_apps.smbs_base.storage.OverwriteStorage(), upload_to=smbs_apps.smbs_base.models.theme_path),
        ),
    ]
