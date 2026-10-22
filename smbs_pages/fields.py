"""
Schema fields for widget props.

A widget declares its props once, as a `Schema`. From that declaration the
platform derives the editor's inspector form (`describe()`), validation and
cleaning (`clean()`), defaults (`default()`), the JSON Schema handed to the
LLM as a tool input schema (`json_schema()`), and the media/page references a
document holds (`references()`).

    class Props(fields.Schema):
        heading = fields.Text(max_length=80, required=False)
        items = fields.Repeater(
            fields.Schema(title=fields.Text(max_length=40), body=fields.Text(multiline=True)),
            min_items=2, max_items=8,
        )
"""
import copy
import functools
import json
import re
from pathlib import Path



NOTSET = object()

# Theme colour tokens a Color field accepts besides hex values. They map to
# CSS variables in smbs_pages/static/smbs_pages/sections.css.
COLOR_TOKENS = ('primary', 'secondary', 'accent', 'surface', 'muted', 'text', 'light', 'dark')
HEX_COLOR = re.compile(r'^#(?:[0-9a-fA-F]{3}){1,2}$')
ICON_NAME = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
KEY_REF = re.compile(r'^[A-Za-z0-9_.-]{1,64}$')

RICH_TEXT_TAGS = {
    'p', 'br', 'strong', 'b', 'em', 'i', 'u', 's', 'a', 'ul', 'ol', 'li',
    'h2', 'h3', 'h4', 'blockquote', 'span', 'small', 'code',
}
RICH_TEXT_ATTRIBUTES = {'a': {'href', 'title', 'target'}, 'span': {'class'}}
LINK_SCHEMES = {'http', 'https', 'mailto', 'tel'}


class FieldError(Exception):
    def __init__(self, message, path=''):
        super().__init__(message)
        self.message = message
        self.path = path


class CleanContext:
    """
    Carries options through a clean() pass and collects references.

    `allow_keys`: SiteSpec mode. Media and page references may be string keys
    that `documents.materialize()` resolves to ids later.
    """

    def __init__(self, allow_keys=False):
        self.allow_keys = allow_keys
        self.references = {'media': set(), 'page': set()}

    def reference(self, kind, value, path):
        if isinstance(value, bool):
            raise FieldError(f'Invalid {kind} reference.', path)
        if isinstance(value, int) and value > 0:
            self.references[kind].add(value)
            return value
        if self.allow_keys and isinstance(value, str) and KEY_REF.match(value):
            self.references[kind].add(value)
            return value
        raise FieldError(f'Invalid {kind} reference.', path)


def _join(path, key):
    return f'{path}.{key}' if path else str(key)


class Field:
    type_name = 'field'

    def __init__(self, *, required=True, default=NOTSET, label='', help_text='', ai_hint=''):
        self.required = required
        self._default = default
        self.label = label
        self.help_text = help_text
        self.ai_hint = ai_hint
        self.name = ''

    def default(self):
        if self._default is NOTSET:
            return self.empty_value()
        return copy.deepcopy(self._default)

    def empty_value(self):
        return None

    def is_empty(self, value):
        return value is None or value == ''

    def clean(self, value, ctx, path=''):
        # A missing value takes the declared default; an explicitly empty one
        # (e.g. "" for text) is still subject to `required`.
        if value is None and self._default is not NOTSET:
            return self.default()
        if self.is_empty(value):
            if self.required:
                raise FieldError('This field is required.', path)
            return self.empty_value()
        return self.clean_value(value, ctx, path)

    def clean_value(self, value, ctx, path):
        return value

    def references(self, value):
        return []

    def map_references(self, value, fn):
        """Returns `value` with every media/page reference replaced by fn(kind, reference)."""
        return value

    def json_schema(self):
        schema = self.value_schema()
        if self.label or self.help_text:
            schema['description'] = ' '.join(part for part in (self.label, self.help_text, self.ai_hint) if part)
        elif self.ai_hint:
            schema['description'] = self.ai_hint
        return schema

    def value_schema(self):
        return {}

    def describe(self):
        return {
            'type': self.type_name,
            'label': self.label or self.name.replace('_', ' ').capitalize(),
            'help_text': self.help_text,
            'required': self.required,
            'default': self.default(),
        }


class Text(Field):
    type_name = 'text'

    def __init__(self, *, max_length=255, min_length=0, multiline=False, **kwargs):
        super().__init__(**kwargs)
        self.max_length = max_length
        self.min_length = min_length
        self.multiline = multiline

    def empty_value(self):
        return ''

    def clean_value(self, value, ctx, path):
        if not isinstance(value, str):
            raise FieldError('Must be text.', path)
        value = value.strip()
        if not self.multiline:
            value = ' '.join(value.split())
        if len(value) > self.max_length:
            raise FieldError(f'At most {self.max_length} characters.', path)
        if len(value) < self.min_length:
            raise FieldError(f'At least {self.min_length} characters.', path)
        return value

    def value_schema(self):
        return {'type': 'string', 'maxLength': self.max_length}

    def describe(self):
        return {**super().describe(), 'max_length': self.max_length, 'multiline': self.multiline}


class RichText(Field):
    """HTML limited to a small allow-list; sanitized with nh3 on every clean."""
    type_name = 'rich_text'

    def __init__(self, *, max_length=20000, **kwargs):
        super().__init__(**kwargs)
        self.max_length = max_length

    def empty_value(self):
        return ''

    def clean_value(self, value, ctx, path):
        if not isinstance(value, str):
            raise FieldError('Must be HTML text.', path)
        cleaned = sanitize_html(value)
        if len(cleaned) > self.max_length:
            raise FieldError(f'At most {self.max_length} characters.', path)
        return cleaned

    def value_schema(self):
        return {
            'type': 'string',
            'maxLength': self.max_length,
            'description': 'HTML using only: ' + ', '.join(sorted(RICH_TEXT_TAGS)) + '.',
        }


def sanitize_html(value):
    # Imported here so sites that only use the legacy widget tree don't need nh3.
    import nh3
    return nh3.clean(
        value,
        tags=RICH_TEXT_TAGS,
        attributes=RICH_TEXT_ATTRIBUTES,
        url_schemes=LINK_SCHEMES,
        link_rel='noopener noreferrer',
    ).strip()


class Number(Field):
    type_name = 'number'

    def __init__(self, *, min_value=None, max_value=None, integer=True, **kwargs):
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value
        self.integer = integer

    def clean_value(self, value, ctx, path):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise FieldError('Must be a number.', path)
        if self.integer:
            if isinstance(value, float) and not value.is_integer():
                raise FieldError('Must be a whole number.', path)
            value = int(value)
        if self.min_value is not None and value < self.min_value:
            raise FieldError(f'Must be at least {self.min_value}.', path)
        if self.max_value is not None and value > self.max_value:
            raise FieldError(f'Must be at most {self.max_value}.', path)
        return value

    def value_schema(self):
        schema = {'type': 'integer' if self.integer else 'number'}
        if self.min_value is not None:
            schema['minimum'] = self.min_value
        if self.max_value is not None:
            schema['maximum'] = self.max_value
        return schema

    def describe(self):
        return {**super().describe(), 'min': self.min_value, 'max': self.max_value, 'integer': self.integer}


class Bool(Field):
    type_name = 'bool'

    def __init__(self, **kwargs):
        kwargs.setdefault('required', False)
        kwargs.setdefault('default', False)
        super().__init__(**kwargs)

    def empty_value(self):
        return False

    def clean_value(self, value, ctx, path):
        if not isinstance(value, bool):
            raise FieldError('Must be true or false.', path)
        return value

    def value_schema(self):
        return {'type': 'boolean'}


class Choice(Field):
    type_name = 'choice'

    def __init__(self, options, **kwargs):
        self.options = [option if isinstance(option, (tuple, list)) else (option, str(option).replace('_', ' ').capitalize())
                        for option in options]
        if 'default' not in kwargs and self.options:
            kwargs['default'] = self.options[0][0]
        super().__init__(**kwargs)

    @property
    def values(self):
        return [value for value, _ in self.options]

    def clean_value(self, value, ctx, path):
        if value not in self.values:
            raise FieldError(f'Must be one of {self.values}.', path)
        return value

    def value_schema(self):
        return {'enum': self.values}

    def describe(self):
        return {**super().describe(), 'options': [{'value': v, 'label': label} for v, label in self.options]}


class Color(Field):
    type_name = 'color'

    def __init__(self, **kwargs):
        kwargs.setdefault('required', False)
        super().__init__(**kwargs)

    def empty_value(self):
        return ''

    def clean_value(self, value, ctx, path):
        if value in COLOR_TOKENS or (isinstance(value, str) and HEX_COLOR.match(value)):
            return value
        raise FieldError(f'Must be a theme colour ({", ".join(COLOR_TOKENS)}) or a hex value.', path)

    def value_schema(self):
        return {'anyOf': [{'enum': list(COLOR_TOKENS)}, {'type': 'string', 'pattern': HEX_COLOR.pattern}]}


@functools.cache
def icon_names():
    """Names in the vendored Bootstrap Icons set (static/smbs_pages/vendor/bootstrap-icons)."""
    path = Path(__file__).parent / 'static/smbs_pages/vendor/bootstrap-icons/bootstrap-icons.json'
    with open(path) as f:
        return frozenset(json.load(f))


class Icon(Field):
    """A Bootstrap Icons name, e.g. "telephone" or "check-circle"."""
    type_name = 'icon'

    def empty_value(self):
        return ''

    def clean_value(self, value, ctx, path):
        if not isinstance(value, str) or not ICON_NAME.match(value) or value not in icon_names():
            raise FieldError(f'{value!r} is not a Bootstrap Icons name.', path)
        return value

    def value_schema(self):
        return {'type': 'string', 'pattern': ICON_NAME.pattern, 'description': 'A Bootstrap Icons name, e.g. "star".'}


class Image(Field):
    """
    {"media": <Media id, or a SiteSpec media key>, "alt": "...", "focal_point": {"x": 0-1, "y": 0-1}}
    Alt text is required whenever an image is set.
    """
    type_name = 'image'

    def clean_value(self, value, ctx, path):
        if not isinstance(value, dict):
            raise FieldError('Must be an image.', path)
        unknown = set(value) - {'media', 'alt', 'focal_point'}
        if unknown:
            raise FieldError(f'Unknown image keys {sorted(unknown)}.', path)
        media = ctx.reference('media', value.get('media'), _join(path, 'media'))
        alt = value.get('alt')
        if not isinstance(alt, str) or not alt.strip():
            raise FieldError('Alt text is required.', _join(path, 'alt'))
        cleaned = {'media': media, 'alt': ' '.join(alt.split())[:250]}
        focal = value.get('focal_point')
        if focal is not None:
            if (not isinstance(focal, dict) or set(focal) != {'x', 'y'}
                    or not all(isinstance(focal[k], (int, float)) and 0 <= focal[k] <= 1 for k in ('x', 'y'))):
                raise FieldError('Focal point must be {"x": 0-1, "y": 0-1}.', _join(path, 'focal_point'))
            cleaned['focal_point'] = {'x': focal['x'], 'y': focal['y']}
        return cleaned

    def references(self, value):
        return [('media', value['media'])] if value else []

    def map_references(self, value, fn):
        return {**value, 'media': fn('media', value['media'])} if value else value

    def value_schema(self):
        return {
            'type': 'object',
            'properties': {
                'media': {'type': ['integer', 'string'], 'description': 'Media id or SiteSpec media key.'},
                'alt': {'type': 'string', 'maxLength': 250, 'description': 'Describes the image for screen readers.'},
            },
            'required': ['media', 'alt'],
            'additionalProperties': False,
        }


class Link(Field):
    """
    {"kind": "page", "page": <Page id or SiteSpec page key>}
    {"kind": "url", "url": "https://..."} · {"kind": "email", "email": "..."}
    {"kind": "tel", "tel": "+1..."} · {"kind": "anchor", "anchor": "contact"}
    Any kind may add "new_tab": true.
    """
    type_name = 'link'
    KINDS = ('page', 'url', 'email', 'tel', 'anchor')
    EMAIL = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
    TEL = re.compile(r'^\+?[0-9 ().-]{3,32}$')
    ANCHOR = re.compile(r'^[A-Za-z][A-Za-z0-9_-]{0,63}$')

    def clean_value(self, value, ctx, path):
        if not isinstance(value, dict) or value.get('kind') not in self.KINDS:
            raise FieldError(f'Link kind must be one of {list(self.KINDS)}.', path)
        kind = value['kind']
        target = value.get(kind)
        target_path = _join(path, kind)
        if kind == 'page':
            target = ctx.reference('page', target, target_path)
        elif kind == 'url':
            if not isinstance(target, str) or not (target.startswith(('https://', 'http://')) or
                                                   (target.startswith('/') and not target.startswith('//'))):
                raise FieldError('URL must start with https://, http:// or /.', target_path)
        elif kind == 'email':
            if not isinstance(target, str) or not self.EMAIL.match(target):
                raise FieldError('Invalid email address.', target_path)
        elif kind == 'tel':
            if not isinstance(target, str) or not self.TEL.match(target):
                raise FieldError('Invalid phone number.', target_path)
        elif kind == 'anchor':
            if not isinstance(target, str) or not self.ANCHOR.match(target):
                raise FieldError('Invalid anchor.', target_path)
        cleaned = {'kind': kind, kind: target}
        if value.get('new_tab'):
            cleaned['new_tab'] = True
        return cleaned

    def references(self, value):
        return [('page', value['page'])] if value and value.get('kind') == 'page' else []

    def map_references(self, value, fn):
        if value and value.get('kind') == 'page':
            return {**value, 'page': fn('page', value['page'])}
        return value

    def value_schema(self):
        return {
            'type': 'object',
            'properties': {
                'kind': {'enum': list(self.KINDS)},
                'page': {'type': ['integer', 'string'], 'description': 'Page id or SiteSpec page key.'},
                'url': {'type': 'string'},
                'email': {'type': 'string'},
                'tel': {'type': 'string'},
                'anchor': {'type': 'string'},
                'new_tab': {'type': 'boolean'},
            },
            'required': ['kind'],
            'additionalProperties': False,
        }


class Schema(Field):
    """
    An object of named fields. Subclass it to declare fields as attributes,
    or pass fields as keyword arguments.
    """
    type_name = 'object'
    declared_fields = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        declared = {}
        for base in reversed(cls.__mro__[1:]):
            declared.update(getattr(base, 'declared_fields', {}))
        for name, value in list(cls.__dict__.items()):
            if isinstance(value, Field):
                declared[name] = value
        cls.declared_fields = declared

    def __init__(self, required=True, **fields):
        super().__init__(required=required)
        self.fields = {}
        for name, field in {**self.declared_fields, **fields}.items():
            field = copy.copy(field)
            field.name = name
            self.fields[name] = field

    def default(self):
        return {name: field.default() for name, field in self.fields.items()}

    def empty_value(self):
        return self.default()

    def is_empty(self, value):
        return value is None

    def clean_value(self, value, ctx, path):
        if not isinstance(value, dict):
            raise FieldError('Must be an object.', path)
        unknown = set(value) - set(self.fields)
        if unknown:
            raise FieldError(f'Unknown fields {sorted(unknown)}.', path)
        cleaned, errors = {}, []
        for name, field in self.fields.items():
            try:
                cleaned[name] = field.clean(value.get(name), ctx, _join(path, name))
            except FieldErrors as exc:
                errors.extend(exc.errors)
            except FieldError as exc:
                errors.append(exc)
        if errors:
            raise FieldErrors(errors)
        return cleaned

    def references(self, value):
        refs = []
        for name, field in self.fields.items():
            if value and value.get(name) is not None:
                refs.extend(field.references(value[name]))
        return refs

    def map_references(self, value, fn):
        if not value:
            return value
        return {name: (field.map_references(value[name], fn) if value.get(name) is not None else value.get(name))
                for name, field in self.fields.items() if name in value}

    def value_schema(self):
        return {
            'type': 'object',
            'properties': {name: field.json_schema() for name, field in self.fields.items()},
            'required': [name for name, field in self.fields.items() if field.required],
            'additionalProperties': False,
        }

    def describe(self):
        return {**super().describe(), 'fields': {name: field.describe() for name, field in self.fields.items()}}


class Repeater(Field):
    """A list of items that all share one schema, e.g. features or testimonials."""
    type_name = 'repeater'

    def __init__(self, item, *, min_items=0, max_items=24, **kwargs):
        kwargs.setdefault('required', min_items > 0)
        super().__init__(**kwargs)
        self.item = item
        self.min_items = min_items
        self.max_items = max_items

    def empty_value(self):
        return []

    def is_empty(self, value):
        return value is None

    def clean_value(self, value, ctx, path):
        if not isinstance(value, list):
            raise FieldError('Must be a list.', path)
        if len(value) < self.min_items:
            raise FieldError(f'Needs at least {self.min_items} items.', path)
        if len(value) > self.max_items:
            raise FieldError(f'At most {self.max_items} items.', path)
        cleaned, errors = [], []
        for index, item in enumerate(value):
            try:
                cleaned.append(self.item.clean(item, ctx, _join(path, index)))
            except FieldErrors as exc:
                errors.extend(exc.errors)
            except FieldError as exc:
                errors.append(exc)
        if errors:
            raise FieldErrors(errors)
        return cleaned

    def references(self, value):
        refs = []
        for item in value or []:
            refs.extend(self.item.references(item))
        return refs

    def map_references(self, value, fn):
        return [self.item.map_references(item, fn) for item in value or []]

    def value_schema(self):
        return {
            'type': 'array',
            'items': self.item.json_schema(),
            'minItems': self.min_items,
            'maxItems': self.max_items,
        }

    def describe(self):
        return {**super().describe(), 'item': self.item.describe(), 'min_items': self.min_items, 'max_items': self.max_items}


class FieldErrors(FieldError):
    """Several field errors from one clean() pass."""

    def __init__(self, errors):
        self.errors = errors
        super().__init__('; '.join(f'{error.path}: {error.message}' if error.path else error.message
                                   for error in errors))
