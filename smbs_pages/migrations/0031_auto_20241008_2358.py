# Generated by Django 3.1.4 on 2024-10-08 23:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smbs_pages', '0030_auto_20231213_0458'),
    ]

    operations = [
        migrations.AlterField(
            model_name='template',
            name='file',
            field=models.FileField(upload_to='smbs_pages/templates'),
        ),
        migrations.AlterField(
            model_name='widget',
            name='type',
            field=models.CharField(choices=[('smbs_apps.smbs_blog.smbs_widgets.blog_posts', 'Blog Posts'), ('smbs_apps.smbs_pages.smbs_widgets.headline', 'Headline'), ('smbs_apps.smbs_pages.smbs_widgets.html', 'Raw HTML'), ('smbs_apps.smbs_pages.smbs_widgets.image', 'Image'), ('smbs_apps.smbs_pages.smbs_widgets.markdown', 'Markdown'), ('smbs_apps.smbs_pages.smbs_widgets.paragraph', 'Paragraph'), ('smbs_apps.smbs_forms.smbs_widgets.contact_address_form', 'Contact Form With Address'), ('smbs_apps.smbs_forms.smbs_widgets.contact_form', 'Contact Form')], max_length=128),
        ),
    ]