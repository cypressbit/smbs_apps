# Generated by Django 2.1.4 on 2019-01-11 04:21

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('smbs_blog', '0006_post_metadata'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='metadata',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict),
        ),
    ]
