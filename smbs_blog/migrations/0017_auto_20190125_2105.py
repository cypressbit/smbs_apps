# Generated by Django 2.1.4 on 2019-01-25 21:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smbs_blog', '0016_auto_20190125_0418'),
    ]

    operations = [
        migrations.RenameField(
            model_name='postcomment',
            old_name='date',
            new_name='created',
        ),
        migrations.AddField(
            model_name='postcomment',
            name='updated',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
