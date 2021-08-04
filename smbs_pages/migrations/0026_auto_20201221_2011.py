# Generated by Django 3.1.1 on 2020-12-21 20:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smbs_pages', '0025_auto_20201221_1952'),
    ]

    operations = [
        migrations.AlterField(
            model_name='widget',
            name='type',
            field=models.CharField(choices=[('smbs_blog.smbs_widgets.blog_posts', 'Blog Posts'), ('smbs_pages.smbs_widgets.headline', 'Headline'), ('smbs_pages.smbs_widgets.html', 'Raw HTML'), ('smbs_pages.smbs_widgets.image', 'Image'), ('smbs_pages.smbs_widgets.markdown', 'Markdown'), ('smbs_pages.smbs_widgets.paragraph', 'Paragraph'), ('smbs_inventory.smbs_widgets.inventory_items', 'Inventory Items'), ('smbs_forms.smbs_widgets.contact_address_form', 'Contact Form With Address'), ('smbs_forms.smbs_widgets.contact_form', 'Contact Form')], max_length=128),
        ),
    ]
