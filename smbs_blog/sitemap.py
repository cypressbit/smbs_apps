from django.contrib.sitemaps import Sitemap

from smbs_blog.models import Post


class BlogSitemap(Sitemap):
    priority = 0.5
    changefreq = 'weekly'

    def items(self):
        return Post.objects.filter(is_draft=False).order_by('-publish_date')

    def lastmod(self, obj):
        return obj.updated
