from django.contrib import admin

from smbs_base.admin import SettingsAdmin

from smbs_inventory.models import Item, Category, InventorySettings


class InventorySettingsAdmin(SettingsAdmin):
    pass


class ItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'id', 'slug', 'cover_image')


admin.site.register(Item, ItemAdmin)
admin.site.register(Category)
admin.site.register(InventorySettings, InventorySettingsAdmin)
