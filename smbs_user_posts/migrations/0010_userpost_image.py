# Generated by Django 3.0.3 on 2020-02-22 00:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smbs_user_posts', '0009_userpostsettings'),
    ]

    operations = [
        migrations.AddField(
            model_name='userpost',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='user_posts'),
        ),
    ]
