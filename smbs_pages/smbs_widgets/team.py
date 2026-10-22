from smbs_apps.smbs_pages import fields
from smbs_apps.smbs_pages.widgets import BaseWidget


class Team(BaseWidget):
    key = 'team'
    NAME = 'Team'
    category = 'content'
    icon = 'people'
    description = 'People with photo, role and a short bio.'
    ai_hint = 'Only include people named in the brief.'
    template = 'smbs_widgets/v2/team.html'

    class Props(fields.Schema):
        columns = fields.Choice([3, 2, 4])
        members = fields.Repeater(
            fields.Schema(
                name=fields.Text(max_length=80, default='Team member'),
                role=fields.Text(max_length=80, required=False),
                bio=fields.Text(max_length=400, multiline=True, required=False),
                photo=fields.Image(required=False),
            ),
            min_items=1, max_items=24,
            default=[{'name': 'Team member', 'role': 'Founder', 'bio': '', 'photo': None}],
        )
