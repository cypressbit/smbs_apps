# Generated by Django 2.1.4 on 2019-02-14 08:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smbs_cities_light', '0002_auto_20190205_0936'),
    ]

    operations = [
        migrations.AddField(
            model_name='city',
            name='population',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='city',
            name='timezone',
            field=models.CharField(blank=True, max_length=24, null=True),
        ),
        migrations.AddField(
            model_name='country',
            name='code',
            field=models.CharField(default='MX', max_length=2, unique=True),
            preserve_default=False,
        ),
    ]
