# Generated by Django 2.1.4 on 2020-01-11 07:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smbs_pages', '0005_auto_20200111_0642'),
    ]

    operations = [
        migrations.AlterField(
            model_name='column',
            name='name',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='container',
            name='name',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='media',
            name='name',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='row',
            name='name',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='widget',
            name='name',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
    ]
