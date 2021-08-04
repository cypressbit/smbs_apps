# Generated by Django 2.1.4 on 2019-01-27 04:33

from django.db import migrations
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('smbs_qa', '0003_auto_20190127_0409'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='tags',
            field=taggit.managers.TaggableManager(help_text='A list of comma-separated tags related to your question, for example "health, fitness".', through='taggit.TaggedItem', to='taggit.Tag', verbose_name='Tags'),
        ),
    ]
