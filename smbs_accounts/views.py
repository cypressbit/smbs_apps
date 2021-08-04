import logging

from django.views.generic.edit import FormView

from django.contrib.auth import login, authenticate
from django.shortcuts import redirect, reverse
from django.conf import settings

from smbs_accounts.forms import SMBSUserCreationForm
from smbs_accounts.models import AccountSettings


logger = logging.getLogger('smbs-debug')


class SignUpView(FormView):
    template_name = 'smbs_accounts/signup.html'
    form_class = SMBSUserCreationForm

    @staticmethod
    def user_profile_enabled():
        return 'smbs_profile' in settings.INSTALLED_APPS

    @staticmethod
    def get_profile_url():
        return reverse('smbs_profile:update')

    def form_valid(self, form):
        form.save()
        username = form.cleaned_data.get('username')
        raw_password = form.cleaned_data.get('password1')
        user = authenticate(username=username, password=raw_password)
        login(self.request, user)

        if self.user_profile_enabled():
            return redirect(self.get_profile_url())
        else:
            return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super(SignUpView, self).get_context_data(**kwargs)
        context['next'] = self.request.GET.get('next', '')
        account_settings = AccountSettings.get_object()
        if account_settings:
            context['terms_of_service'] = account_settings.terms_of_service
            context['privacy_policy'] = account_settings.privacy_policy
        return context

    def get_success_url(self):
        next_url = self.request.POST.get('next')
        account_settings = AccountSettings.get_object()
        if next_url:
            return next_url
        elif account_settings and account_settings.signup_redirect:
            return account_settings.signup_redirect.get_absolute_url()
        return '/'
