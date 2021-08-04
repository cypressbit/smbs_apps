from django.utils.safestring import mark_safe


class Widget:

    NAME = 'Headline'

    def __init__(self, **kwargs):
        self.options = kwargs.get('options', {})
        self.content = kwargs.get('content', '')
        self.classes = kwargs.get('classes', '')

    def render(self):
        headline_type = self.options.get('headline_type', 'h1')
        return mark_safe('<{headline_type} class="{classes}">{content}</{headline_type}>'.format(
            headline_type=headline_type, content=mark_safe(self.content), classes=self.classes))
