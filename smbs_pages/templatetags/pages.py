from django import template, forms


register = template.Library()


@register.simple_tag(takes_context=True)
def render_widget(context, widget):
    return widget.render(context)
