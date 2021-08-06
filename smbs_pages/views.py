from django.shortcuts import get_object_or_404

from django.views.generic import DetailView

from smbs_apps.smbs_pages.models import Page


class PageDetailView(DetailView):

    model = Page

    def get_object(self):
        if not self.kwargs:
            return get_object_or_404(Page, active=True, slug=None)
        slug = self.kwargs.get('slug')
        parent_slug = self.kwargs.get('parent_slug')
        grand_parent_slug = self.kwargs.get('grand_parent_slug')
        page = get_object_or_404(Page,
                                 active=True,
                                 slug=slug,
                                 parent__slug=parent_slug,
                                 parent__parent__slug=grand_parent_slug)
        return page
