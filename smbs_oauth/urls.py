from django.urls import path

from smbs_apps.smbs_oauth.views import GoogleCallbackView, GoogleLoginRedirectView


app_name = 'smbs_oauth'


urlpatterns = [
    path('google/login/', GoogleLoginRedirectView.as_view(), name='google_login'),
    path('google/callback/', GoogleCallbackView.as_view(), name='google_callback'),
]
