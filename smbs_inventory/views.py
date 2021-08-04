from django.views.generic.list import ListView
from django.views.generic.detail import DetailView

from smbs_base.views import SMBSView, SMBSObjectMetadataView
from smbs_inventory.models import Item


class ItemListView(SMBSView, ListView):
    model = Item
    name = 'item'


class ItemDetailView(SMBSObjectMetadataView, DetailView):
    model = Item
