from django.utils.safestring import mark_safe


class Widget:

    NAME = 'Image'

    def __init__(self, **kwargs):
        self.content = kwargs.get('content', '')
        self.classes = kwargs.get('classes', '')
        self.media = kwargs.get('media', [])

    def render(self):
        img_str = ''
        for m in self.media.all():
            img_str += '<img class="{}" src="{}" />'.format(self.classes, m.file.url)
        return mark_safe(img_str)
