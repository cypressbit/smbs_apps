from django.urls import path

from smbs_contact.views import ContactView


app_name = 'smbs_contact'


urlpatterns = [
    path('', ContactView.as_view(), name='contact'),
]
