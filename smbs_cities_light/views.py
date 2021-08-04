from django.views.generic.list import ListView
from django.views.generic.detail import DetailView

from smbs_cities_light import Country, State, City


class CountryListView(ListView):
    model = Country


class CountryDetailView(DetailView):
    model = Country


class StateDetailView(DetailView):
    model = State


class CityDetailView(DetailView):
    model = City
