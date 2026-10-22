from django.http import Http404
from django.shortcuts import get_object_or_404

from django.views.generic import DetailView

from smbs_apps.smbs_base.views import SMBSObjectMetadataView

from smbs_apps.smbs_pages import rendering, services
from smbs_apps.smbs_pages.models import Page, SiteChrome


class PageDetailView(SMBSObjectMetadataView, DetailView):

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

    renders_document = False

    def is_preview(self):
        token = self.request.GET.get('preview')
        return bool(token) and services.check_preview_token(token, self.object)

    def get_template_names(self):
        if self.renders_document:
            return ['smbs_pages/page_document.html']
        return super().get_template_names()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        preview = self.is_preview()
        # A legacy page being converted can be previewed as a document before publishing.
        if not (self.object.is_document or (preview and self.object.draft.get('sections'))):
            return context
        self.renders_document = True
        if preview:
            document = self.object.draft
        elif self.object.published_revision_id:
            document = self.object.published_revision.document
        else:
            raise Http404('This page has not been published.')
        render_context = {'request': self.request, 'page': self.object, 'preview': preview}
        chrome = SiteChrome.get_object()
        chrome_document = (chrome.draft if preview else chrome.published) if chrome else None
        context.update({
            'is_preview': preview,
            'document_html': rendering.render_document(document, render_context),
            'chrome_header_html': rendering.render_document(chrome_document['header'], render_context)
            if chrome_document and chrome_document.get('header', {}).get('sections') else None,
            'chrome_footer_html': rendering.render_document(chrome_document['footer'], render_context)
            if chrome_document and chrome_document.get('footer', {}).get('sections') else None,
        })
        return context
