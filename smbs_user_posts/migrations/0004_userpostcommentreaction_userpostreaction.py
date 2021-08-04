# Generated by Django 2.1.4 on 2019-12-27 01:35

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('smbs_user_posts', '0003_auto_20191226_1001'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserPostCommentReaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('reaction', models.CharField(choices=[('angry', 'Angry'), ('sad', 'Sad'), ('happy', 'Happy'), ('thumbs_up', 'thumbs_up'), ('thumbs_down', 'thumbs_down')], default='thumbs_up', max_length=12)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('user_post_comment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='smbs_user_posts.UserPostComment')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='UserPostReaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('reaction', models.CharField(choices=[('angry', 'Angry'), ('sad', 'Sad'), ('happy', 'Happy'), ('thumbs_up', 'thumbs_up'), ('thumbs_down', 'thumbs_down')], default='thumbs_up', max_length=12)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('user_post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='smbs_user_posts.UserPost')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
