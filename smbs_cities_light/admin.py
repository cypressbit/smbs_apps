from django.contrib import admin

from smbs_apps.smbs_cities_light.models import Country, State, City


class CountryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']


class StateAdmin(admin.ModelAdmin):
    list_display = ['name']


class CityAdmin(admin.ModelAdmin):
    ordering = ['population']
    search_fields = ['name', 'state__name']
    list_display = ['id', 'state', 'name', 'population', 'latitude', 'longitude']


admin.site.register(Country, CountryAdmin)
admin.site.register(State, StateAdmin)
admin.site.register(City, CityAdmin)
