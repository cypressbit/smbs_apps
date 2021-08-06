from django.urls import path

from smbs_apps.smbs_forms.views import contact


app_name = 'smbs_forms'


urlpatterns = [
    path('contact/', contact, name='contact'),
]
