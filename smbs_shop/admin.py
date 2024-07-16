from django.contrib import admin
from smbs_apps.smbs_shop.models import (ShopSettings, ShopCategory, ShopItem, ShopItemReview,
                                        ShopCart, ShopCartItem, ShopOrder, ShopOrderItem, ShopPayment)
from smbs_apps.smbs_custom_attrs.models import CustomAttribute


# Use this as a mixin to store common logic.
class TimestampModelAdmin(admin.ModelAdmin):
    readonly_fields = ('created', 'updated')


class CustomAttributeInline(admin.TabularInline):
    model = CustomAttribute
    extra = 1


# Inherit the mixin.
class ShopCategoryAdmin(TimestampModelAdmin):
    list_display = ('title', 'slug', 'user', 'created', 'updated')


# Inherit the mixin.
class ShopItemAdmin(TimestampModelAdmin):
    list_display = ('title', 'slug', 'category', 'price', 'stock_quantity', 'is_in_stock', 'publish_date')
    list_filter = ('category', 'is_in_stock', 'is_featured', 'is_visible', 'publish_date')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'category', 'description', 'cover_image', 'price', 'discount_price',
                       'stock_quantity', 'is_in_stock', 'is_featured', 'is_visible', 'publish_date', 'tags')
        }),
    )
    inlines = [CustomAttributeInline]


# Inherit the mixin.
class ShopOrderAdmin(TimestampModelAdmin):
    list_display = ('user', 'total_price', 'status', 'created', 'updated')
    list_filter = ('status', 'created', 'updated')


# Inherit the mixin.
class ShopPaymentAdmin(TimestampModelAdmin):
    list_display = ('order', 'amount', 'payment_method', 'payment_status', 'created')
    list_filter = ('payment_status', 'created')


# Inherit the mixin.
class ShopItemReviewAdmin(TimestampModelAdmin):
    list_display = ('user', 'get_shop_item_title', 'positive_review', 'created', 'updated')
    list_filter = ('positive_review', 'created', 'updated')

    def get_shop_item_title(self, obj):
        return obj.shop_item.title
    get_shop_item_title.short_description = 'Shop Item'


admin.site.register(ShopSettings)
admin.site.register(ShopCategory, ShopCategoryAdmin)
admin.site.register(ShopItem, ShopItemAdmin)
admin.site.register(ShopCart)
admin.site.register(ShopCartItem)
admin.site.register(ShopOrder, ShopOrderAdmin)
admin.site.register(ShopOrderItem)
admin.site.register(ShopPayment, ShopPaymentAdmin)
admin.site.register(ShopItemReview, ShopItemReviewAdmin)
