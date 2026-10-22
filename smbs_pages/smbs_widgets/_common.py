"""Schema pieces shared by several widgets (not a widget module itself)."""
from smbs_apps.smbs_pages import fields


def button_item(default_label='Get in touch'):
    return fields.Schema(
        label=fields.Text(max_length=40, default=default_label),
        link=fields.Link(default={'kind': 'anchor', 'anchor': 'contact'}),
        style=fields.Choice(['primary', 'secondary', 'accent', 'link']),
        icon=fields.Icon(required=False),
    )


def buttons(min_items=0, max_items=2, default_label='Get in touch', with_default=True):
    default = [{'label': default_label, 'link': {'kind': 'anchor', 'anchor': 'contact'},
                'style': 'primary', 'icon': ''}] if with_default else []
    return fields.Repeater(button_item(default_label), min_items=min_items, max_items=max_items,
                           required=False, default=default, label='Buttons')
