from django.urls import path

from smbs_apps.smbs_managed import views


app_name = 'smbs_managed'

urlpatterns = [
    path('sso/', views.sso_login, name='sso'),
    path('api/materialize/', views.materialize, name='materialize'),
    path('api/status/', views.status, name='status'),
]
