# Generated by Django 2.1.4 on 2019-08-18 22:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smbs_base', '0004_auto_20190818_1025'),
    ]

    operations = [
        migrations.AlterField(
            model_name='objectmetadata',
            name='expiration_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='objectmetadata',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='smbs_base/metadata'),
        ),
        migrations.AlterField(
            model_name='objectmetadata',
            name='modified_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='objectmetadata',
            name='published_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='viewmetadata',
            name='expiration_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='viewmetadata',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='smbs_base/metadata'),
        ),
        migrations.AlterField(
            model_name='viewmetadata',
            name='modified_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='viewmetadata',
            name='published_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
