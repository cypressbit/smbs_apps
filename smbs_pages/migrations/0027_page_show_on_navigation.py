# Generated by Django 3.1.4 on 2021-02-04 23:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smbs_pages', '0026_auto_20201221_2011'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='show_on_navigation',
            field=models.BooleanField(default=True),
        ),
    ]
