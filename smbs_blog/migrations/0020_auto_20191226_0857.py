# Generated by Django 2.1.4 on 2019-12-26 08:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('smbs_blog', '0019_post_metadata'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='postcomment',
            name='reactions',
        ),
        migrations.RemoveField(
            model_name='postcomment',
            name='reactions_count',
        ),
    ]
