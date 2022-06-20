from django.urls import path, include
from django.contrib.auth import views
from django.urls import reverse_lazy
from smbs_apps.smbs_accounts.views import SignUpView


app_name = 'smbs_accounts'


urlpatterns = [
    path('login/', views.LoginView.as_view(template_name='smbs_accounts/login.html'), name='login'),
    path('logout/', views.LogoutView.as_view(template_name='smbs_accounts/logout.html'), name='logout'),

    path('password_change/', views.PasswordChangeView.as_view(), name='password_change'),
    path('password_change/done/', views.PasswordChangeDoneView.as_view(), name='password_change_done'),

    path('password_reset/', views.PasswordResetView.as_view(success_url=reverse_lazy('smbs_accounts:password_reset_done')), name='password_reset'),
    path('password_reset/done/', views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.PasswordResetConfirmView.as_view(success_url=reverse_lazy('smbs_accounts:password_reset_complete')), name='password_reset_confirm'),
    path('reset/done/', views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    path('signup/', SignUpView.as_view(), name='signup'),
]
