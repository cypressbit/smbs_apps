from django.shortcuts import redirect

from django.views.generic.edit import CreateView, UpdateView


class CommentCreateView(CreateView):

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.user = self.request.user
        model_field_id = '{}_id'.format(form.cleaned_data['model_field_name'])
        setattr(instance, model_field_id, form.cleaned_data['model_instance_id'])
        instance.save()

        return redirect(instance.get_absolute_url())
