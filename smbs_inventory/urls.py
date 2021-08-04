from django.urls import path, re_path

from smbs_inventory.views import ItemListView, ItemDetailView


app_name = 'smbs_inventory'


urlpatterns = [
    path('', ItemListView.as_view(), name='item-list'),
    re_path(r'^(?P<slug>[\w-]+)/$', ItemDetailView.as_view(), name='item-detail'),
]
