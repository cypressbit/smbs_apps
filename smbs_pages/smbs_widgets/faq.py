from smbs_apps.smbs_pages import fields
from smbs_apps.smbs_pages.widgets import BaseWidget


class Faq(BaseWidget):
    key = 'faq'
    NAME = 'FAQ'
    category = 'content'
    icon = 'question-circle'
    description = 'Frequently asked questions as an accordion.'
    ai_hint = 'Questions real customers ask before buying. Answers short and factual; no invented policies or prices.'
    template = 'smbs_widgets/v2/faq.html'

    class Props(fields.Schema):
        items = fields.Repeater(
            fields.Schema(
                question=fields.Text(max_length=200, default='A common question?'),
                answer=fields.RichText(default='<p>A short, clear answer.</p>'),
            ),
            min_items=1, max_items=20,
            default=[{'question': 'A common question?', 'answer': '<p>A short, clear answer.</p>'}],
        )
        open_first = fields.Bool(label='Open the first answer')
