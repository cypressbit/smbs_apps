from smbs_apps.smbs_pages import fields
from smbs_apps.smbs_pages.widgets import BaseWidget


class RawHtml(BaseWidget):
    """Unescaped HTML. Staff only by design: hidden from customers and the AI."""
    key = 'raw_html'
    NAME = 'Raw HTML'
    category = 'advanced'
    icon = 'code-slash'
    description = 'Custom HTML (staff only).'
    staff_only = True
    template = 'smbs_widgets/v2/raw_html.html'

    class Props(fields.Schema):
        html = fields.Text(max_length=200000, multiline=True, required=False)
