from smbs_apps.smbs_pages import fields
from smbs_apps.smbs_pages.widgets import BaseWidget


class LogoCloud(BaseWidget):
    key = 'logo_cloud'
    NAME = 'Logos'
    category = 'media'
    icon = 'award'
    description = 'A row of client, partner or certification logos.'
    ai_hint = 'Only logos the business provided; never invent clients or certifications.'
    template = 'smbs_widgets/v2/logo_cloud.html'

    class Props(fields.Schema):
        heading = fields.Text(max_length=80, required=False)
        grayscale = fields.Bool(default=True)
        logos = fields.Repeater(
            fields.Schema(image=fields.Image(required=False), link=fields.Link(required=False)),
            min_items=1, max_items=16,
            default=[{'image': None, 'link': None}],
        )
