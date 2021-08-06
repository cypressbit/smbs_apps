from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from smbs_apps.smbs_base.models import TimestampModel


class Reaction(TimestampModel):
    ANGRY = 'angry'
    SAD = 'sad'
    HAPPY = 'happy'
    THUMBS_UP = 'thumbs_up'
    THUMBS_DOWN = 'thumbs_down'
    LOL = 'lol'
    LOVE = 'love'

    REACTIONS = [
        (ANGRY, _('Angry')),
        (SAD, _('Sad')),
        (HAPPY, _('Happy')),
        (THUMBS_UP, _('thumbs_up')),
        (THUMBS_DOWN, _('thumbs_down')),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reaction = models.CharField(max_length=12, choices=REACTIONS, default=THUMBS_UP)

    class Meta:
        abstract = True

