# Generated by Django 2.1.4 on 2019-12-29 07:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smbs_user_posts', '0007_auto_20191229_0307'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userpostcomment',
            name='reaction_count',
            field=models.IntegerField(default=0),
        ),
    ]
