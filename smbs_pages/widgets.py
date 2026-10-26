"""
Widget discovery and the widget API.

Every installed app may ship widgets as modules in an `smbs_widgets` package.
Two kinds are discovered there:

- **Schema widgets** (v2): subclasses of `BaseWidget` with a stable `key` and
  a `Props` schema (see `fields.py`). They render props from a page document.
- **Legacy widgets**: a module-level `Widget` class with `NAME` and a
  `render()` method, used by the relational Container/Row/Column/Widget tree.
  The legacy `Widget.type` model field stores their module path.

Discovery is lazy and cached; nothing is imported at module import time, so
widgets may import models freely.
"""
import functools
import importlib
import logging
import pkgutil

from django.apps import apps
from django.template import loader

from smbs_apps.smbs_pages import fields


logger = logging.getLogger(__name__)


class BaseWidget:
    """
    Base class for schema widgets. Subclasses set `key` (stored in documents,
    never change it), `NAME`, `template`, and a nested `Props` schema.
    """
    key = None
    NAME = ''
    category = 'content'   # palette group: basic | content | media | social-proof | forms | blog | commerce
    icon = 'square'        # Bootstrap Icons name for the palette
    description = ''
    ai_hint = ''           # how the AI should fill this widget
    capability = None      # e.g. "blog": hidden unless the site enables that capability
    staff_only = False     # hidden from customers and the AI (e.g. raw HTML)
    template = None

    class Props(fields.Schema):
        pass

    def __init__(self, props, context=None, node=None):
        self.props = props
        self.context = context if context is not None else {}
        self.node = node or {}

    @classmethod
    def schema(cls):
        # Cached per class (not inherited), since subclasses declare their own Props.
        if '_schema' not in cls.__dict__:
            cls._schema = cls.Props()
        return cls._schema

    @classmethod
    def defaults(cls):
        return cls.schema().default()

    @classmethod
    def clean_props(cls, props, ctx=None):
        return cls.schema().clean(props, ctx or fields.CleanContext())

    @classmethod
    def json_schema(cls):
        schema = cls.schema().value_schema()
        if cls.ai_hint or cls.description:
            schema['description'] = cls.ai_hint or cls.description
        return schema

    @classmethod
    def describe(cls):
        return {
            'key': cls.key,
            'name': cls.NAME,
            'category': cls.category,
            'icon': cls.icon,
            'description': cls.description,
            'capability': cls.capability,
            'staff_only': cls.staff_only,
            'schema': cls.schema().describe(),
            'defaults': cls.defaults(),
        }

    def get_context_data(self):
        return {'props': self.props, 'widget': self, 'node': self.node, 'request': self.context.get('request'),
                'editing': bool(self.context.get('editing'))}

    def render(self):
        return loader.render_to_string(self.template, self.get_context_data(), request=self.context.get('request'))


class _MediaList:
    """Mimics the `media` related manager legacy widgets expect (`.all()`)."""

    def __init__(self, ids):
        self.ids = ids

    def all(self):
        from smbs_apps.smbs_pages.models import Media
        media = {m.id: m for m in Media.objects.filter(id__in=self.ids)}
        return [media[i] for i in self.ids if i in media]


class LegacyWidgetAdapter(BaseWidget):
    """
    Wraps a legacy widget module so converted pages can keep using it from a
    document. Its key is the legacy module path; staff only, since the content
    is raw markup.
    """
    category = 'legacy'
    staff_only = True
    module = None

    class Props(fields.Schema):
        content = fields.Text(required=False, max_length=200000, multiline=True)
        classes = fields.Text(required=False)
        options = fields.Field(required=False, default={})
        media = fields.Field(required=False, default=[])

    @classmethod
    @functools.cache
    def for_module(cls, module):
        return type(f'Legacy_{module.__name__.replace(".", "_")}', (cls,), {
            'key': module.__name__,
            'NAME': f'{module.Widget.NAME} (legacy)',
            'module': module,
        })

    def render(self):
        widget = self.module.Widget(
            content=self.props.get('content') or '',
            media=_MediaList(self.props.get('media') or []),
            classes=self.props.get('classes') or '',
            options=self.props.get('options') or {},
            context=self.context,
        )
        return widget.render()


def _widget_modules():
    for app_config in apps.get_app_configs():
        package_name = f'{app_config.name}.smbs_widgets'
        if importlib.util.find_spec(package_name) is None:
            continue
        package = importlib.import_module(package_name)
        for module_info in pkgutil.iter_modules(package.__path__, package.__name__ + '.'):
            try:
                yield importlib.import_module(module_info.name)
            except Exception:
                logger.exception('Could not import widget module %s', module_info.name)


@functools.cache
def _discover():
    schema_widgets, legacy_modules = {}, {}
    for module in _widget_modules():
        found_schema_widget = False
        for value in vars(module).values():
            if (isinstance(value, type) and issubclass(value, BaseWidget) and value.key
                    and value.__module__ == module.__name__ and not issubclass(value, LegacyWidgetAdapter)):
                if value.key in schema_widgets:
                    raise RuntimeError(f'Duplicate widget key {value.key!r} in {module.__name__}')
                schema_widgets[value.key] = value
                found_schema_widget = True
        legacy = getattr(module, 'Widget', None)
        if not found_schema_widget and legacy is not None and hasattr(legacy, 'NAME'):
            legacy_modules[module.__name__] = module
    return schema_widgets, legacy_modules


def get_registry():
    """Schema widgets by key."""
    return _discover()[0]


def get_widget(key):
    """The widget class for a document node type: a schema widget key or a legacy module path."""
    schema_widgets, legacy_modules = _discover()
    if key in schema_widgets:
        return schema_widgets[key]
    if key in legacy_modules:
        return LegacyWidgetAdapter.for_module(legacy_modules[key])
    return None


def catalog(capabilities=None, include_staff_only=False):
    """Describes available schema widgets for the editor palette and the AI."""
    return [
        widget.describe() for widget in get_registry().values()
        if (include_staff_only or not widget.staff_only)
        and (widget.capability is None or capabilities is None or widget.capability in capabilities)
    ]


def legacy_widget_choices():
    """Choices for the legacy `Widget.type` field. A callable, so migrations don't snapshot it."""
    return [(path, module.Widget.NAME) for path, module in sorted(_discover()[1].items())]


# Backwards-compatible helpers for the legacy widget tree.

def find_widgets():
    return legacy_widget_choices()


def load_widget(name):
    try:
        return importlib.import_module(name)
    except ImportError:
        logger.warning('Widget module %s not found', name)
        return None
