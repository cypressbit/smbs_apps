# Generated by Django 3.1.1 on 2020-09-16 04:15

from django.db import migrations, models
import smbs_base.models
import smbs_base.storage


class Migration(migrations.Migration):

    dependencies = [
        ('smbs_base', '0008_auto_20200310_0822'),
    ]

    operations = [
        migrations.AddField(
            model_name='basesettings',
            name='bootstrap_theme',
            field=models.FileField(blank=True, null=True, storage=smbs_base.storage.OverwriteStorage(), upload_to=smbs_base.models.bootstrap_theme_path),
        ),
    ]
