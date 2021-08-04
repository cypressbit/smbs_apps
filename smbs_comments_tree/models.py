import bleach

from mptt.models import MPTTModel, TreeForeignKey

from django.db import models
from django.contrib.auth.models import User

from smbs_base.models import TimestampModel
from smbs_reactions.mixins import ReactionMixin


class Comment(MPTTModel, TimestampModel, ReactionMixin):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    parent = TreeForeignKey('self',
                            related_name='reply',
                            blank=True,
                            null=True,
                            db_index=True,
                            on_delete=models.CASCADE)
    text = models.TextField()
    reaction_count = models.IntegerField(default=0)
    deleted = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        clean_text = bleach.clean(self.text, strip=True)
        self.text = bleach.linkify(clean_text)
        super(Comment, self).save(*args, **kwargs)

    def __str__(self):
        return self.text

    class Meta:
        abstract = True

    class MPTTMeta:
        order_insertion_by = ['-reaction_count']
