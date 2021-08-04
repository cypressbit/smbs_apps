from django import template, forms


register = template.Library()


@register.filter
def ff_addcss(field, css):
    classes = field.field.widget.attrs.get('class', '')
    field.field.widget.attrs['class'] = '{0} {1}'.format(classes, css)
    return field


@register.filter
def ff_readonly(field):
    field.field.widget.attrs['readonly'] = 'true'
    return field


@register.filter
def ff_hidden(field):
    field.field.widget.attrs['hidden'] = 'true'
    return field


@register.filter
def ff_placeholder(field, value=None):
    text = value or field.label
    if type(field.field) == forms.ModelChoiceField or type(field.field) == forms.TypedChoiceField:
        field.field.empty_label = text
    else:
        field.field.widget.attrs.update({'placeholder': text})
    return field


@register.filter
def ff_type(obj):
    return obj.field.__class__.__name__


@register.filter
def ff_attr(field, attribute):
    attr, value = attribute.split(',', 1)
    field.field.widget.attrs[attr] = value
    return field


@register.filter
def dict_get(dictionary, key):
    return dictionary.get(key)


@register.filter
def space_to_plus(value):
    return value.replace(' ', '+').replace(',', '')
