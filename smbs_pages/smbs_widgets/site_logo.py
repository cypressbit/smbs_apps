from smbs_apps.smbs_pages import fields
from smbs_apps.smbs_pages.models import Media
from smbs_apps.smbs_pages.widgets import BaseWidget


class SiteLogo(BaseWidget):
    key = 'site_logo'
    NAME = 'Logo'
    category = 'basic'
    icon = 'patch-check'
    description = 'Your logo, linking to the home page. Shows the business name until a logo is added.'
    ai_hint = 'The business name, for the header. Leave the logo empty: only the business can provide it.'
    template = 'smbs_widgets/v2/site_logo.html'

    class Props(fields.Schema):
        name = fields.Text(max_length=80, default='Business name', label='Business name')
        logo = fields.Image(required=False)
        height = fields.Choice(['md', 'sm', 'lg'], label='Logo size')

    def get_context_data(self):
        context = super().get_context_data()
        logo = self.props.get('logo')
        context['media'] = Media.objects.filter(pk=logo['media']).first() if logo else None
        return context
