from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView

from .models import InventoryItem, MenuItem, Order


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_active and self.request.user.is_staff


class InventoryListView(LoginRequiredMixin, StaffRequiredMixin, View):
    def get(self, request):
        items = InventoryItem.objects.all().order_by('name')
        return render(request, 'operations/inventory_list.html', {'items': items})

    def post(self, request):
        # Handle restock POST: expects 'item_id' and 'amount'
        item_id = request.POST.get('item_id')
        amount = request.POST.get('amount')
        if not item_id or not amount:
            return redirect(reverse('dashboard-inventory'))

        item = get_object_or_404(InventoryItem, pk=item_id)
        try:
            dec = Decimal(amount)
        except Exception:
            dec = Decimal('0')

        item.quantity += dec
        item.save()
        return redirect(reverse('dashboard-inventory'))


class MenuListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = MenuItem
    template_name = 'operations/menu_list.html'
    context_object_name = 'menu_items'


class OrdersListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = Order
    template_name = 'operations/orders_list.html'
    context_object_name = 'orders'
    ordering = ['-created_at']
