from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smbs_blog', '0029_post_cover_image_alt_text'),
    ]

    operations = [
        migrations.AddField(
            model_name='blogsettings',
            name='posts_per_page',
            field=models.PositiveSmallIntegerField(default=10),
        ),
    ]
