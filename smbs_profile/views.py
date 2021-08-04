from django.views.generic.edit import UpdateView
from django.contrib.sites.models import Site
from django.shortcuts import redirect
from smbs_profile.models import ProfileSettings, LocationProfile


class ProfileUpdateMixin(object):

    def form_valid(self, form):
        form.user = self.request.user
        form.save()


class LocationProfileUpdateView(UpdateView, ProfileUpdateMixin):
    template_name = 'smbs_profile/location_update_form.html'
    model = LocationProfile
    fields = ['city', 'newsletter_signup']

    def get_object(self, queryset=None):
        obj, created = self.model.objects.get_or_create(user=self.request.user)
        return obj

    def get_success_url(self):
        next_url = self.request.POST.get('next', None)
        if next_url:
            return next_url
        return '/'


def profile_update(request):
    site = Site.objects.get_current(request)
    profile_settings, created = ProfileSettings.objects.get_or_create(site=site)
    profile_url_name = 'smbs_profile:{}'.format(profile_settings.user_profile)
    return redirect(profile_url_name)
