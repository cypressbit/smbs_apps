# Generated by Django 3.1.4 on 2023-12-13 04:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smbs_pages', '0029_auto_20221225_0638'),
    ]

    operations = [
        migrations.AlterField(
            model_name='page',
            name='slug',
            field=models.SlugField(allow_unicode=True, blank=True, max_length=255, null=True, unique=True),
        ),
    ]
