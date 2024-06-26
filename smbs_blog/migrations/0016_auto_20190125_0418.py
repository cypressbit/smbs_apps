# Generated by Django 2.1.4 on 2019-01-25 04:18

import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0002_alter_domain_unique'),
        ('smbs_blog', '0015_auto_20190118_0001'),
    ]

    operations = [
        migrations.CreateModel(
            name='BlogSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('comments_enabled', models.BooleanField(default=False)),
                ('minimum_word_count', models.PositiveSmallIntegerField(default=500)),
                ('minimum_tag_count', models.PositiveSmallIntegerField(default=4)),
                ('minimum_internal_link_count', models.PositiveSmallIntegerField(default=1)),
                ('minimum_external_link_count', models.PositiveSmallIntegerField(default=1)),
                ('minimum_image_count', models.PositiveSmallIntegerField(default=1)),
                ('minimum_keyword_count', models.PositiveSmallIntegerField(default=2)),
                ('seo_checks', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(blank=True, choices=[('word_count', 'Word count'), ('tags', 'Tag count'), ('images', 'Image count'), ('internal_links', 'Internal link count'), ('external_links', 'External link count'), ('keywords', 'Keyword count')], max_length=24), default=list, size=None, verbose_name='SEO checks')),
                ('site', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sites.Site')),
            ],
            options={
                'verbose_name': 'Blog Settings',
            },
        ),
        migrations.DeleteModel(
            name='PostSettings',
        ),
    ]
