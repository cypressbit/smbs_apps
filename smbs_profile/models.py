from django.contrib.auth.models import User

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from django.db import models

from smbs_base.models import SettingsModel, TimestampModel
from smbs_cities_light.models import City


class ProfileSettings(SettingsModel):
    LOCATION = 'location'
    PROFILE_CHOICES = (
        (LOCATION, 'Location'),
    )
    user_profile = models.CharField(max_length=24, choices=PROFILE_CHOICES, default=LOCATION)


class BaseProfile(TimestampModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    newsletter_signup = models.BooleanField(default=False)

    class Meta:
        abstract = True


class LocationProfile(BaseProfile):
    city = models.ForeignKey(City, blank=True, null=True, on_delete=models.CASCADE)


class ImageProfile(BaseProfile):
    image = models.ImageField(upload_to='smbs_profile/image_profile/')


class SimpleForumProfile(ImageProfile):
    tagline = models.CharField(max_length=64, blank=-True, null=True)
