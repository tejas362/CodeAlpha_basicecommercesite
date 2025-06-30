from django.contrib import admin
from .models import Product, Order, OrderItem

admin.site.register(Product)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product'] # Useful if you have many products
    extra = 0 # Don't show extra empty forms by default

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'first_name', 'last_name', 'email', 'paid', 'created_at', 'total_paid']
    list_filter = ['paid', 'created_at']
    inlines = [OrderItemInline]
    search_fields = ['id', 'first_name', 'last_name', 'email', 'user__username']
