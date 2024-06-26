# Generated by Django 2.1.4 on 2019-01-19 10:36

from django.db import migrations, models
import smbs_apps.smbs_base.models


class Migration(migrations.Migration):

    dependencies = [
        ('smbs_base', '0003_sitesettings_updated'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sitesettings',
            name='contact_display_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='sitesettings',
            name='contact_email_address',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AlterField(
            model_name='sitesettings',
            name='contact_phone_number',
            field=models.CharField(blank=True, max_length=24, null=True),
        ),
        migrations.AlterField(
            model_name='sitesettings',
            name='email_host',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='sitesettings',
            name='email_password',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='sitesettings',
            name='email_port',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='sitesettings',
            name='email_user',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='sitesettings',
            name='logo',
            field=models.ImageField(blank=True, null=True, upload_to=smbs_apps.smbs_base.models.site_logo_path, validators=[smbs_apps.smbs_base.models.validate_image_extension]),
        ),
    ]
