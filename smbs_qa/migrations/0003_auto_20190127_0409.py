# Generated by Django 2.1.4 on 2019-01-27 04:09

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('smbs_qa', '0002_auto_20190125_2118'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='is_anonymous',
            field=models.BooleanField(default=False, verbose_name='Ask anonymously'),
        ),
        migrations.AlterField(
            model_name='question',
            name='question',
            field=models.TextField(verbose_name='Question'),
        ),
        migrations.AlterField(
            model_name='question',
            name='title',
            field=models.CharField(max_length=255, verbose_name='Title'),
        ),
        migrations.AlterField(
            model_name='question',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User'),
        ),
    ]
