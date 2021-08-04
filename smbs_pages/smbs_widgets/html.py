from django.utils.safestring import mark_safe


class Widget:

    NAME = 'Raw HTML'

    def __init__(self, **kwargs):
        self.content = kwargs.get('content', '')

    def render(self):
        return mark_safe(self.content)
