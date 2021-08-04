from django.shortcuts import redirect
from django.core.mail import send_mail
from django.core.mail.backends.smtp import EmailBackend as SMTPBackend

from smbs_forms.models import ContactFormSettings
from smbs_forms.forms import ContactForm


def contact(request):
    if request.method == 'POST':
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
            return redirect(settings.get('success_url'))

