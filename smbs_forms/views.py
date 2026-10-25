from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl

from django.middleware.csrf import CsrfViewMiddleware
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.core.mail.backends.smtp import EmailBackend as SMTPBackend

from smbs_apps.smbs_forms import turnstile
from smbs_apps.smbs_forms.models import ContactFormSettings
from smbs_apps.smbs_forms.forms import ContactForm


def _back(request, status):
    """The page the form was posted from, with ?contact=<status> so it can show a notice."""
    referer = request.META.get('HTTP_REFERER', '')
    if not url_has_allowed_host_and_scheme(referer, allowed_hosts={request.get_host()},
                                           require_https=request.is_secure()):
        referer = '/'
    parts = urlsplit(referer)
    query = [(k, v) for k, v in parse_qsl(parts.query) if k != 'contact'] + [('contact', status)]
    return urlunsplit(('', '', parts.path or '/', urlencode(query), 'contact'))


@csrf_exempt  # checked below: Turnstile when it's configured, Django's CSRF check otherwise
def contact(request):
    if request.method != 'POST':
        return redirect('/')
    if turnstile.enabled():
        if not turnstile.verify(request):
            return redirect(_back(request, 'error'))
    else:
        rejected = CsrfViewMiddleware(lambda r: None).process_view(request, contact, (), {})
        if rejected is not None:
            return rejected
    form = ContactForm(request.POST)
    if form.is_valid():
        obj = form.save()
        settings = ContactFormSettings.get_settings()
        if settings.get('email_enabled'):
            connection = SMTPBackend(
                use_tls=True,
                host=settings.get('email_host'),
                port=settings.get('email_port'),
                username=settings.get('email_user'),
                password=settings.get('email_password'),
                fail_silently=True
            )
            message = '{}\n{}\n{}\n\n{}'.format(obj.name, obj.email, obj.phone, obj.message)
            send_mail(settings.get('email_subject'),
                      message,
                      obj.email,
                      [settings.get('email_recipient')],
                      connection=connection,
                      fail_silently=True)
        if ContactFormSettings.get_object() and settings.get('success_url') not in (None, '', '/'):
            return redirect(settings.get('success_url'))
        return redirect(_back(request, 'sent'))
    return redirect(_back(request, 'error'))
