# Generated by Django 3.1.1 on 2020-09-22 13:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smbs_inventory', '0002_auto_20200919_0647'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventorysettings',
            name='navigation_slug',
            field=models.CharField(default='products', max_length=32),
        ),
    ]
