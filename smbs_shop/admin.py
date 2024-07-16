from django.contrib import admin
from smbs_apps.smbs_shop.models import (ShopSettings, ShopCategory, ShopItem, ShopItemReview,
                                        ShopCart, ShopCartItem, ShopOrder, ShopOrderItem, ShopPayment)


# Use this as a mixin to store common logic.
class TimestampModelAdmin(admin.ModelAdmin):
    readonly_fields = ('created_at', 'updated_at')


# Inherit the mixin.
class ShopCategoryAdmin(TimestampModelAdmin, admin.ModelAdmin):
    list_display = ('title', 'slug', 'user', 'created_at', 'updated_at')


# Inherit the mixin.
class ShopItemAdmin(TimestampModelAdmin, admin.ModelAdmin):
    list_display = ('title', 'slug', 'category', 'price', 'stock_quantity', 'is_in_stock', 'publish_date')
    list_filter = ('category', 'is_in_stock', 'is_featured', 'is_visible', 'publish_date')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'category', 'description', 'cover_image', 'price', 'discount_price', 'stock_quantity', 'is_in_stock', 'is_featured', 'is_visible', 'publish_date', 'tags', 'custom_attributes')
        }),
    )


# Inherit the mixin.
class ShopOrderAdmin(TimestampModelAdmin, admin.ModelAdmin):
    list_display = ('user', 'total_price', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'updated_at')


# Inherit the mixin.
class ShopPaymentAdmin(TimestampModelAdmin, admin.ModelAdmin):
    list_display = ('order', 'amount', 'payment_method', 'payment_status', 'created_at')
    list_filter = ('payment_status', 'created_at')


# Inherit the mixin.
class ShopItemReviewAdmin(TimestampModelAdmin, admin.ModelAdmin):
    list_display = ('user', 'shop_item', 'positive_review', 'created_at', 'updated_at')
    list_filter = ('positive_review', 'created_at', 'updated_at')


admin.site.register(ShopSettings)
admin.site.register(ShopCategory, ShopCategoryAdmin)
admin.site.register(ShopItem, ShopItemAdmin)
admin.site.register(ShopCart)
admin.site.register(ShopCartItem)
admin.site.register(ShopOrder, ShopOrderAdmin)
admin.site.register(ShopOrderItem)
admin.site.register(ShopPayment, ShopPaymentAdmin)
admin.site.register(ShopItemReview, ShopItemReviewAdmin)
