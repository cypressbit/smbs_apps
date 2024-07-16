from django.contrib import admin
from smbs_apps.smbs_shop.models import (ShopSettings, ShopCategory, ShopItem, ShopItemReview,
                                        ShopCart, ShopCartItem, ShopOrder, ShopOrderItem, ShopPayment)


@admin.register(ShopSettings)
class ShopSettingsAdmin(admin.ModelAdmin):
    list_display = ('navigation_title', 'navigation_slug', 'page_title', 'enable_custom_attribute_filtering')
    fieldsets = (
        (None, {
            'fields': ('navigation_title', 'navigation_slug', 'page_title')
        }),
        ('Payment Settings', {
            'fields': ('enable_paypal', 'paypal_client_id', 'paypal_client_secret', 'paypal_mode', 'paypal_webhook_id',
                       'enable_stripe', 'stripe_api_key', 'stripe_publishable_key', 'stripe_webhook_secret')
        }),
        ('Custom Attributes', {
            'fields': ('enable_custom_attribute_filtering', 'custom_attribute_filters')
        }),
    )


@admin.register(ShopCategory)
class ShopCategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'user', 'created_at', 'updated_at')


@admin.register(ShopItem)
class ShopItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'category', 'price', 'stock_quantity', 'is_in_stock', 'publish_date')
    list_filter = ('category', 'is_in_stock', 'is_featured', 'is_visible', 'publish_date')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'category', 'description', 'cover_image', 'price', 'discount_price', 'stock_quantity', 'is_in_stock', 'is_featured', 'is_visible', 'publish_date', 'tags', 'custom_attributes')
        }),
    )


@admin.register(ShopCart)
class ShopCartAdmin(admin.ModelAdmin):
    pass


@admin.register(ShopCartItem)
class ShopCartItemAdmin(admin.ModelAdmin):
    pass


@admin.register(ShopOrder)
class ShopOrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_price', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'updated_at')


@admin.register(ShopOrderItem)
class ShopOrderItemAdmin(admin.ModelAdmin):
    pass


@admin.register(ShopPayment)
class ShopPaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'amount', 'payment_method', 'payment_status', 'created_at')
    list_filter = ('payment_status', 'created_at')


@admin.register(ShopItemReview)
class ShopItemReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'shop_item', 'positive_review', 'created_at', 'updated_at')
    list_filter = ('positive_review', 'created_at', 'updated_at')