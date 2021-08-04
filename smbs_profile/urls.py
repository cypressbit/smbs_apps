from django.urls import path
from django.contrib.auth.decorators import login_required

from smbs_profile.views import profile_update, LocationProfileUpdateView


app_name = 'smbs_profile'


urlpatterns = [
    path('update/', login_required(profile_update), name='update'),
    path('update/location/', login_required(LocationProfileUpdateView.as_view()), name='location'),
]
