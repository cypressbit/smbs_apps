# Generated by Django 3.0.4 on 2021-07-16 00:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smbs_pages', '0027_page_show_on_navigation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='widget',
            name='type',
            field=models.CharField(choices=[('smbs_blog.smbs_widgets.blog_posts', 'Blog Posts'), ('smbs_pages.smbs_widgets.headline', 'Headline'), ('smbs_pages.smbs_widgets.html', 'Raw HTML'), ('smbs_pages.smbs_widgets.image', 'Image'), ('smbs_pages.smbs_widgets.markdown', 'Markdown'), ('smbs_pages.smbs_widgets.paragraph', 'Paragraph')], max_length=128),
        ),
    ]
