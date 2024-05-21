import os
import shutil
import zipfile

from collections import OrderedDict

import yaml

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from django.urls import reverse
from django.db import models
from django.db.models import JSONField
from django.core import management

from smbs_apps.smbs_base.models import SiteModel, TimestampModel, ObjectMetadata
from smbs_apps.smbs_pages.widgets import discovered_widgets, load_widget


class Template(SiteModel, TimestampModel):
    TEMPLATE_PATH = 'smbs_pages/templates/{}'

    file = models.FileField(upload_to='smbs_pages/files')
    name = models.CharField(max_length=64, blank=True, null=True)
    version = models.CharField(max_length=16, blank=True, null=True)
    is_installed = models.BooleanField(default=False)

    @property
    def template_data(self):
        if not getattr(self, '_template_data'):
            if self.is_installed:
                self._template_data = self.load_template_file()
            else:
                self._template_data = None
        return self._template_data

    @property
    def template_path(self):
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, self.TEMPLATE_PATH.format(self.id))

    def load_template_file(self):
        data = yaml.load(open(self.template_path + 'template.yaml', 'rb'), Loader=Loader)
        return data

    def install(self):
        self.unzip()
        self.add_static_files()
        self.is_installed = True
        self.version = self.template_data.get('version')
        self.save()

    def apply(self):
        self.create_pages()

    def unzip(self):
        source = self.file.path
        with zipfile.ZipFile(source, 'r') as zip_file:
            zip_file.extractall(self.template_path)

    def add_static_files(self):
        source = self.template_path + '/static'
        if os.path.isdir(source):
            destination = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static')
            shutil.copytree(source, destination, dirs_exist_ok=True)
            management.call_command('collectstatic')

    def create_pages(self):
        pages = self.template_data.get('pages')
        for p in pages:
            page = Page(
                template=self,
                parent=p.get('parent'),
                name=p.get('name'),
                navigation_order=p.get('navigation_order'),
                slug=p.get('slug'),
                active=True
            )
            page.save()
            column = self.create_boilerplate(p.get('name'))
            content = None
            if p.get('source'):
                with open(os.path.join(self.template_path, p.get('source'))) as f:
                    content = f.read()
            widget = Widget(
                column=column,
                name=p.get('name'),
                content=content,
                type='html',
                active=True
            )
            widget.save()

    def create_boilerplate(self, name=None):
        container = Container(page=self.id, name=name, active=True)
        container.save()
        row = Row(name=name, container=container, active=True)
        row.save()
        column = Column(name=name, row=row, active=True)
        column.save()
        return column


class Page(SiteModel, TimestampModel):
    metadata = models.ForeignKey(ObjectMetadata, on_delete=models.DO_NOTHING,
                                 blank=True, null=True)
    template = models.ForeignKey(Template, blank=True, null=True, on_delete=models.DO_NOTHING)
    parent = models.ForeignKey('self', blank=True, null=True, on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True, null=True, unique=True)
    active = models.BooleanField(default=False)
    show_on_navigation = models.BooleanField(default=True)
    navigation_order = models.PositiveSmallIntegerField(blank=True, null=True)

    def __str__(self):
        return self.name or str(self.id)

    def get_content_tree(self):
        tree = OrderedDict()
        containers = self.container_set.filter(active=True).order_by('position')
        tree['containers'] = OrderedDict((c, c.get_content_tree()) for c in containers)
        return tree

    def get_all_parents(self):
        parents = []
        current_parent = self.parent
        while current_parent is not None:
            parents.append(current_parent)
            current_parent = current_parent.parent
        return parents

    def has_child_pages(self):
        return self.page_set.exists()

    def get_child_pages(self):
        pages = self.page_set.filter(site=self.site).order_by('navigation_order')
        return pages

    def get_absolute_url(self):
        args = [self.slug]
        args.extend([p.slug for p in self.get_all_parents()])
        url = reverse('smbs_pages:page-detail', args=reversed([a for a in args if a]))
        return url

    def save(self, *args, **kwargs):
        parents = self.get_all_parents()
        if len(parents) >= 2:
            raise Exception('Page depth not supported')
        else:
            super(Page, self).save(*args, **kwargs)


class Media(TimestampModel):
    IMAGE = 'image'
    VIDEO = 'video'
    AUDIO = 'audio'
    DOCUMENT = 'document'

    TYPES = [
        (IMAGE, 'Image'),
        (VIDEO, 'Video'),
        (AUDIO, 'Audio'),
        (DOCUMENT, 'Document'),
    ]

    name = models.CharField(max_length=128, blank=True, null=True)
    file = models.FileField(upload_to='page/media/')

    def __str__(self):
        return self.name or str(self.id)


class StyleModel(models.Model):
    custom_classes = models.CharField(max_length=255, blank=True, null=True)
    custom_css = models.TextField(blank=True, null=True)

    class Meta:
        abstract = True


class PositionModel(models.Model):

    class Positions(models.IntegerChoices):
        ABOVE = 1
        LEFT = 2
        RIGHT = 3
        BELOW = 4

    position_reference = models.ForeignKey('self', on_delete=models.DO_NOTHING, blank=True, null=True)
    position = models.PositiveSmallIntegerField(choices=Positions.choices, default=0)

    class Meta:
        abstract = True


class Container(TimestampModel, StyleModel, PositionModel):
    page = models.ManyToManyField(Page)
    name = models.CharField(max_length=128, blank=True, null=True)
    active = models.BooleanField(default=True)

    def get_content_tree(self):
        tree = OrderedDict()
        rows = self.row_set.filter(active=True).order_by('position')
        tree['rows'] = OrderedDict((r, r.get_content_tree()) for r in rows)
        return tree

    def __str__(self):
        return self.name or str(self.id)


class Row(TimestampModel, StyleModel, PositionModel):
    container = models.ManyToManyField(Container)
    name = models.CharField(max_length=128, blank=True, null=True)
    active = models.BooleanField(default=True)

    def get_content_tree(self):
        tree = OrderedDict()
        columns = self.column_set.filter(active=True).order_by('position')
        tree['columns'] = OrderedDict((c, c.get_content_tree()) for c in columns)
        return tree

    def __str__(self):
        return self.name or str(self.id)


class Column(TimestampModel, StyleModel, PositionModel):

    class Widths(models.IntegerChoices):
        W14 = 3, '25%'
        W12 = 6, '50%'
        W34 = 9, '75%'
        W44 = 12, '100%'

    row = models.ManyToManyField(Row)
    name = models.CharField(max_length=128, blank=True, null=True)
    width = models.PositiveSmallIntegerField(choices=Widths.choices, default=Widths.W44)
    mobile_width = models.PositiveSmallIntegerField(choices=Widths.choices, default=Widths.W44)
    active = models.BooleanField(default=True)

    def get_content_tree(self):
        parents = [[w, w.get_content_tree(column=self)] for w
                   in self.widget_set.filter(active=True, position_reference=None).order_by('position')]
        results = self.flatten(parents)
        return results

    def flatten(self, nest):
        for i in nest:
            if isinstance(i, (list, tuple)):
                yield from self.flatten(i)
            else:
                yield i

    def __str__(self):
        return self.name or str(self.id)


class Widget(TimestampModel, StyleModel, PositionModel):

    type = models.CharField(max_length=128, choices=discovered_widgets)
    column = models.ManyToManyField(Column, blank=True)
    name = models.CharField(max_length=128, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    media = models.ManyToManyField(Media, blank=True)
    active = models.BooleanField(default=True)
    options = JSONField(default=dict, blank=True, null=True )

    def render(self, context=None):
        widget_module = load_widget(self.type)
        if widget_module:
            widget = widget_module.Widget(content=self.content,
                                          media=self.media,
                                          classes=self.custom_classes,
                                          options=self.options,
                                          context=context)
            return widget.render()
        return ''

    def get_content_tree(self, column):
        widget_list = [[w, w.get_content_tree(column)] for w
                       in Widget.objects.filter(active=True, column=column,
                                                position_reference=self).order_by('position')]
        return widget_list

    def __str__(self):
        return self.name or str(self.id)



