from django.template import loader

from smbs_apps.smbs_blog.models import Post


class Widget:

    NAME = 'Blog Posts'

    def __init__(self, **kwargs):
        self.options = kwargs.get('options', {})

    def render(self):
        blog_posts = self.options.get('blog_posts', 6)
        posts = Post.objects.filter(is_draft=False)[:int(blog_posts)]
        template_file = 'smbs_widgets/blog_posts.html'
        template = loader.get_template(template_file)
        return template.render({'blog_posts': posts})
