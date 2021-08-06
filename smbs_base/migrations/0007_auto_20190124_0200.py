# Generated by Django 2.1.4 on 2019-01-24 02:00

from django.db import migrations, models
import smbs_apps.smbs_base.models
import smbs_apps.smbs_base.storage


class Migration(migrations.Migration):

    dependencies = [
        ('smbs_base', '0006_auto_20190120_2030'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sitesettings',
            name='custom_css',
            field=models.FileField(blank=True, null=True, storage=smbs_apps.smbs_base.storage.OverwriteStorage(), upload_to=smbs_apps.smbs_base.models.site_css_path),
        ),
        migrations.AlterField(
            model_name='sitesettings',
            name='logo',
            field=models.FileField(blank=True, null=True, storage=smbs_apps.smbs_base.storage.OverwriteStorage(), upload_to=smbs_apps.smbs_base.models.site_logo_path, validators=[smbs_apps.smbs_base.models.validate_image_extension]),
        ),
    ]
