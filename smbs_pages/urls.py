from django.urls import path

from smbs_apps.smbs_pages.views import PageDetailView


app_name = 'smbs_apps.smbs_pages'


urlpatterns = [
    path('', PageDetailView.as_view(), name='page-detail'),
    path('<str:slug>/', PageDetailView.as_view(), name='page-detail'),
    path('<str:parent_slug>/<str:slug>/', PageDetailView.as_view(), name='page-detail'),
    path('<str:grand_parent_slug>/<str:parent_slug>/<str:slug>/', PageDetailView.as_view(), name='page-detail'),
]
