from django.urls import path

from smbs_apps.smbs_forms.views import contact, turnstile_frame


app_name = 'smbs_forms'


urlpatterns = [
    path('contact/', contact, name='contact'),
    path('turnstile/', turnstile_frame, name='turnstile'),
]
