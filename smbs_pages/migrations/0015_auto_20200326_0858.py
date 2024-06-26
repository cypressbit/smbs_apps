# Generated by Django 3.0.4 on 2020-03-26 08:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smbs_pages', '0014_auto_20200210_2050'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='htmlwidget',
            name='widget_ptr',
        ),
        migrations.RemoveField(
            model_name='markdownwidget',
            name='widget_ptr',
        ),
        migrations.RemoveField(
            model_name='paragraphwidget',
            name='widget_ptr',
        ),
        migrations.AddField(
            model_name='widget',
            name='type',
            field=models.CharField(choices=[('html', 'Raw HTML'), ('markdown', 'Markdown'), ('paragraph', 'Paragraph'), ('headline', 'Headline')], default='paragraph', max_length=16),
        ),
        migrations.DeleteModel(
            name='HeadlineWidget',
        ),
        migrations.DeleteModel(
            name='HTMLWidget',
        ),
        migrations.DeleteModel(
            name='MarkdownWidget',
        ),
        migrations.DeleteModel(
            name='ParagraphWidget',
        ),
    ]
