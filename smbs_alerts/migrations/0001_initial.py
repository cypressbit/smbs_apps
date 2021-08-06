# Generated by Django 2.1.4 on 2019-03-18 02:17

from django.db import migrations, models
import django.db.models.deletion
import smbs_apps.smbs_alerts.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('sites', '0002_alter_domain_unique'),
    ]

    operations = [
        migrations.CreateModel(
            name='Alert',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('alert_type', models.CharField(choices=[('success', 'Success'), ('warning', 'Warning'), ('info', 'Info'), ('danger', 'Danger')], default='success', max_length=24)),
                ('title', models.CharField(max_length=128)),
                ('content', models.TextField()),
                ('position', models.CharField(choices=[('top', 'Top'), ('bottom', 'Bottom')], default='top', max_length=24)),
                ('site', models.ForeignKey(default=smbs_apps.smbs_alerts.models.get_current_site, on_delete=django.db.models.deletion.CASCADE, to='sites.Site')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
