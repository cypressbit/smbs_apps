from django.contrib import admin
from smbs_apps.smbs_shop.models import (ShopSettings, ShopCategory, ShopItem, ShopItemReview,
                                        ShopCart, ShopCartItem, ShopOrder, ShopOrderItem, ShopPayment)


@admin.register(ShopSettings)
class ShopSettingsAdmin(admin.ModelAdmin):
    list_display = ['navigation_title', 'navigation_slug', 'page_title', 'enable_paypal', 'enable_stripe']


@admin.register(ShopCategory)
class ShopCategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'user']
    search_fields = ['title', 'slug', 'description']
    prepopulated_fields = {'slug': ('title',)}


@admin.register(ShopItem)
class ShopItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'price', 'stock_quantity', 'is_in_stock', 'is_featured', 'is_visible', 'publish_date']
    list_filter = ['is_in_stock', 'is_featured', 'is_visible', 'publish_date', 'category']
    search_fields = ['title', 'description', 'sku']
    prepopulated_fields = {'slug': ('title',)}
    autocomplete_fields = ['category', 'tags', 'user']


@admin.register(ShopItemReview)
class ShopItemReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'inventory_item', 'positive_review', 'comment']
    search_fields = ['user__username', 'inventory_item__title', 'comment']


class ShopCartItemInline(admin.TabularInline):
    model = ShopCartItem
    extra = 1


@admin.register(ShopCart)
class ShopCartAdmin(admin.ModelAdmin):
    list_display = ['user']
    inlines = [ShopCartItemInline]


class ShopOrderItemInline(admin.TabularInline):
    model = ShopOrderItem
    extra = 1


@admin.register(ShopOrder)
class ShopOrderAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_price', 'status']
    list_filter = ['status']
    search_fields = ['user__username', 'total_price']
    inlines = [ShopOrderItemInline]


@admin.register(ShopPayment)
class ShopPaymentAdmin(admin.ModelAdmin):
    list_display = ['order', 'amount', 'payment_method', 'payment_status']
    list_filter = ['payment_method', 'payment_status']
    search_fields = ['order__id', 'amount', 'payment_method']
