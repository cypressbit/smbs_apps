from smbs_apps.smbs_pages import fields
from smbs_apps.smbs_pages.widgets import BaseWidget


class Steps(BaseWidget):
    key = 'steps'
    NAME = 'Steps'
    category = 'content'
    icon = 'list-ol'
    description = 'A numbered process: how it works.'
    ai_hint = '3–4 steps from first contact to result. Titles are 2–4 words.'
    template = 'smbs_widgets/v2/steps.html'

    class Props(fields.Schema):
        items = fields.Repeater(
            fields.Schema(
                title=fields.Text(max_length=60, default='A step'),
                body=fields.Text(max_length=240, multiline=True, required=False),
            ),
            min_items=2, max_items=6,
            default=[
                {'title': 'Get in touch', 'body': 'Tell us what you need.'},
                {'title': 'Get a plan', 'body': 'We suggest the best option and a clear price.'},
                {'title': 'Enjoy the result', 'body': 'We do the work and follow up.'},
            ],
        )
