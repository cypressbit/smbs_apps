from django.contrib import admin

from smbs_apps.smbs_shop.models import (ShopSettings, Category, Item, ItemReview,
                                        Cart, CartItem, Order, OrderItem, Payment)


@admin.register(ShopSettings)
class ShopSettingsAdmin(admin.ModelAdmin):
    list_display = ['navigation_title', 'navigation_slug', 'page_title', 'enable_paypal', 'enable_stripe']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'user']
    search_fields = ['title', 'slug', 'description']
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'price', 'stock_quantity', 'is_in_stock', 'is_featured', 'is_visible', 'publish_date']
    list_filter = ['is_in_stock', 'is_featured', 'is_visible', 'publish_date', 'category']
    search_fields = ['title', 'description', 'sku']
    prepopulated_fields = {'slug': ('title',)}
    autocomplete_fields = ['category', 'tags', 'user']


@admin.register(ItemReview)
class ItemReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'inventory_item', 'positive_review', 'comment']
    search_fields = ['user__username', 'inventory_item__title', 'comment']


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user']
    inlines = [CartItemInline]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_price', 'status']
    list_filter = ['status']
    search_fields = ['user__username', 'total_price']
    inlines = [OrderItemInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['order', 'amount', 'payment_method', 'payment_status']
    list_filter = ['payment_method', 'payment_status']
    search_fields = ['order__id', 'amount', 'payment_method']