from django.contrib import admin
from .models import (RestaurantTable, MenuItem, InventoryItem, 
                     Order, OrderItem, Recipe, Reservation)
from django.db.models import Sum

# Register your models here.
class RecipeInline(admin.TabularInline):
    model = Recipe
    extra = 1

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    inlines = [RecipeInline]
    list_display = ('name', 'price', 'category')

@admin.register(InventoryItem)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'quantity', 'unit', 'min_stock_limit', 'status_check')
    list_filter = ('unit',)
    search_fields = ('name',)

    def status_check(self, obj):
        # use the model property which returns a friendly emoji + text
        return obj.status_color
    status_check.short_description = 'Stock status'

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    fields = ('menu_item', 'quantity')
    readonly_fields = ()

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'table', 'status', 'total_amount', 'created_at')
    readonly_fields = ('total_amount',)
    list_filter = ('status', 'created_at')
    search_fields = ('table__number',)
    inlines = [OrderItemInline]

    def save_model(self, request, obj, form, change):
        # Save the order itself; total_amount is readonly and will be
        # calculated by signals when OrderItems are saved/removed.
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formset, change):
        # Let Django save inline OrderItems first (this will trigger signals
        # that recalculate totals and modify inventory). After related items
        # are saved, refresh the order instance so the admin shows the updated total.
        super().save_related(request, form, formset, change)
        try:
            obj = form.instance
            obj.refresh_from_db()
        except Exception:
            pass


admin.site.register(RestaurantTable)
admin.site.register(Reservation)