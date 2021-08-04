import markdown


class Widget:

    NAME = 'Markdown'

    def __init__(self, **kwargs):
        self.content = kwargs.get('content', '')

    def render(self):
        return markdown.markdown(self.content)
