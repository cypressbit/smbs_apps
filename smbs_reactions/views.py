from django.http import JsonResponse
from django.views.generic.edit import CreateView, UpdateView

from smbs_base.views import JSONResponseMixin


class ReactionCreateView(CreateView, JSONResponseMixin):

    update_count = False
    parent = None

    def form_invalid(self, form):
        response = super().form_invalid(form)
        if self.request.is_ajax():
            return JsonResponse(form.errors, status=400)
        else:
            return response

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.user = self.request.user
        instance.save()
        if self.update_count and self.parent:
            parent_instance = getattr(instance, self.parent)
            parent_instance.reaction_count += 1
            parent_instance.save()
        return self.render_to_response({'id': instance.id})

    def render_to_response(self, context, **response_kwargs):
        return self.render_to_json_response(context, **response_kwargs)
