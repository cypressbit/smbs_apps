# Generated by Django 2.1.4 on 2019-10-17 00:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('smbs_pages', '0001_initial'),
        ('sites', '0002_alter_domain_unique'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccountSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('privacy_policy', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='smbs_pages.Page')),
                ('site', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sites.Site')),
                ('terms_of_service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='smbs_pages.Page')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
