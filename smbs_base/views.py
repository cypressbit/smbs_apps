from django.http import JsonResponse
from django.views.generic.base import TemplateView
from django.urls import reverse_lazy, reverse

from smbs_apps.smbs_base.models import ViewMetadata


class SMBSPage(type):

    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'pages'):
            # This branch only executes when processing the mount point itself.
            # So, since this is a new plugin type, not an implementation, this
            # class shouldn't be registered as a plugin. Instead, it sets up a
            # list where plugins can be registered later.
            cls.pages = []
        else:
            # This must be a plugin implementation, which should be registered.
            # Simply appending it to the list is all that's needed to keep
            # track of it later.
            cls.pages.append(cls)


class SMBSView(metaclass=SMBSPage):

    name = None

    def get_context_data(self, *args, **kwargs):
        context = super(SMBSView, self).get_context_data(*args, **kwargs)
        try:
            metadata = ViewMetadata.objects.filter(view=self.name).latest()
        except ViewMetadata.DoesNotExist:
            metadata = None
        context['metadata'] = metadata
        return context


class SMBSTemplateView(SMBSView, TemplateView):
    pass


class SMBSObjectMetadataView:

    def get_context_data(self, *args, **kwargs):
        context = super(SMBSObjectMetadataView, self).get_context_data(*args, **kwargs)
        context['metadata'] = self.object.metadata
        return context


class JSONResponseMixin:
    """
    A mixin that can be used to render a JSON response.
    """
    def render_to_json_response(self, context, **response_kwargs):
        """
        Returns a JSON response, transforming 'context' to make the payload.
        """
        return JsonResponse(
            self.get_data(context),
            **response_kwargs
        )

    def get_data(self, context):
        """
        Returns an object that will be serialized as JSON by json.dumps().
        """
        return context
