from django.contrib.sites.models import Site

from smbs_apps.smbs_blog.models import Post
from smbs_apps.smbs_pages import fields
from smbs_apps.smbs_pages.widgets import BaseWidget


class LatestPosts(BaseWidget):
    key = 'latest_posts'
    NAME = 'Latest blog posts'
    category = 'blog'
    icon = 'journal-text'
    description = 'The newest published blog posts.'
    ai_hint = 'Add only when the site has a blog.'
    capability = 'blog'
    template = 'smbs_widgets/v2/latest_posts.html'

    class Props(fields.Schema):
        heading = fields.Text(max_length=100, required=False, default='From the blog')
        count = fields.Number(min_value=3, max_value=12, default=3)
        layout = fields.Choice(['cards', 'list'])

    def get_context_data(self):
        context = super().get_context_data()
        context['posts'] = (Post.objects.filter(site=Site.objects.get_current(), is_draft=False)
                            .order_by('-publish_date')[:self.props['count']])
        return context
