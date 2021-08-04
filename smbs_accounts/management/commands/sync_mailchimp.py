import requests
from mailchimp3 import MailChimp
from mailchimp3.mailchimpclient import MailChimpError

from django.conf import settings
from django.core.management.base import BaseCommand

from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Syncs user emails with a mailchimp list'

    def handle(self, *args, **options):
        users = User.objects.filter(is_active=True)
        self.stdout.write('Syncing {} users'.format(users.count()))

        client = MailChimp(settings.MAILCHIMP_KEY, settings.MAILCHIMP_USER)

        email_count = 0
        error_count = 0
        for user in users:
            if user.email:
                try:
                    client.lists.members.create(
                        settings.MAILCHIMP_DEFAULT_LIST, {
                            'email_address': user.email,
                            'status': 'subscribed',
                            'merge_fields': {
                                'FNAME': user.first_name,
                                'LNAME': user.last_name,
                            },
                        })
                    email_count += 1
                except requests.exceptions.HTTPError:
                    error_count += 1
                    message = 'Failed to add email {}'.format(user.email)
                    self.stdout.write(self.style.ERROR(message))
                except MailChimpError:
                    error_count += 1
                    message = 'Invalid email {}'.format(user.email)
                    self.stdout.write(self.style.ERROR(message))

        error_message = '{} emails skipped due to errors'.format(error_count)
        self.stdout.write(self.style.WARNING(error_message))
        success_message = 'Synced {} email addresses'.format(email_count)
        self.stdout.write(self.style.SUCCESS(success_message))
