from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify

from django.db import models

from smbs_apps.smbs_base.models import TimestampModel


class Country(TimestampModel):
    name = models.CharField(max_length=100, verbose_name=_('Name'))
    code = models.CharField(max_length=2, unique=True)
    slug = models.SlugField(max_length=100, editable=False)

    class Meta:
        verbose_name = _('Country')

    def __str__(self):
        return self.name

    def states(self):
        return self.state_set.all()

    def clean(self):
        self.slug = slugify(self.name)
        self.code = self.code.upper()


class State(TimestampModel):
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, verbose_name=_('Name'))
    slug = models.SlugField(max_length=100, editable=False)

    class Meta:
        verbose_name = _('State or region')

    def __str__(self):
        return self.name

    def cities(self):
        return self.city_set.all()

    def clean(self):
        self.slug = slugify(self.name)


class City(TimestampModel):
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, verbose_name=_('Name'))
    slug = models.SlugField(max_length=100, editable=False)
    population = models.PositiveIntegerField(blank=True, null=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    timezone = models.CharField(max_length=24, blank=True, null=True)

    class Meta:
        verbose_name = _('City')

    def __str__(self):
        return '{}, {}'.format(self.state.name, self.name)

    def clean(self):
        self.slug = slugify(self.name)

    def location(self):
        return self.latitude, self.longitude

    def get_or_create_slug(self):
        if not self.slug:
            slug = slugify(self.name)
            self.slug = slug
            self.save()
        return self.slug
