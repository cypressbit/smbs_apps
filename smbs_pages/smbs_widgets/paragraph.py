from django.utils.safestring import mark_safe


class Widget:

    NAME = 'Paragraph'

    def __init__(self, **kwargs):
        self.content = kwargs.get('content', '')
        self.classes = kwargs.get('classes', '')

    def render(self):
        return mark_safe('<p class="{classes}">{content}</p>'.format(classes=self.classes, content=self.content))
