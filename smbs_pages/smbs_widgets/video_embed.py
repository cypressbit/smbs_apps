import re

from smbs_apps.smbs_pages import fields
from smbs_apps.smbs_pages.widgets import BaseWidget


YOUTUBE = re.compile(r'^https://(?:www\.|m\.)?(?:youtube\.com/(?:watch\?(?:.*&)?v=|embed/|shorts/)|youtu\.be/)([A-Za-z0-9_-]{11})')
VIMEO = re.compile(r'^https://(?:www\.)?(?:player\.)?vimeo\.com/(?:video/)?(\d+)')


def embed_url(url):
    """The privacy-friendly embed URL for a YouTube or Vimeo link, or None."""
    match = YOUTUBE.match(url or '')
    if match:
        return f'https://www.youtube-nocookie.com/embed/{match.group(1)}'
    match = VIMEO.match(url or '')
    if match:
        return f'https://player.vimeo.com/video/{match.group(1)}?dnt=1'
    return None


class VideoUrl(fields.Text):
    """A YouTube or Vimeo link."""

    def clean_value(self, value, ctx, path):
        value = super().clean_value(value, ctx, path)
        if embed_url(value) is None:
            raise fields.FieldError('Must be a YouTube or Vimeo link (https://).', path)
        return value


class VideoEmbed(BaseWidget):
    key = 'video_embed'
    NAME = 'Video'
    category = 'media'
    icon = 'play-btn'
    description = 'An embedded YouTube or Vimeo video.'
    ai_hint = 'Only use a video URL given in the brief.'
    template = 'smbs_widgets/v2/video_embed.html'

    class Props(fields.Schema):
        url = VideoUrl(max_length=300, default='https://www.youtube.com/watch?v=aqz-KE-bpKQ', label='YouTube or Vimeo link')
        title = fields.Text(max_length=120, default='Video')

    def get_context_data(self):
        context = super().get_context_data()
        context['embed_url'] = embed_url(self.props['url'])
        return context
