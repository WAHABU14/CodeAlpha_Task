from decimal import Decimal
from django.test import TestCase

from .models import InventoryItem, MenuItem, Recipe, RestaurantTable, Order
from .serializers import OrderSerializer


class OrderSignalsTestCase(TestCase):
	def setUp(self):
		# create an ingredient and menu/recipe
		self.tomato = InventoryItem.objects.create(
			name='Tomato', quantity=Decimal('10.00'), unit='kg', min_stock_limit=Decimal('2.00')
		)

		self.soup = MenuItem.objects.create(name='Tomato Soup', price=Decimal('5.00'), category='Main')
		Recipe.objects.create(menu_item=self.soup, ingredient=self.tomato, amount_needed=Decimal('0.5'))

		self.table = RestaurantTable.objects.create(number=1, capacity=4, is_available=True)

	def test_creating_order_with_items_reduces_inventory_and_sets_total(self):
		data = {
			'table': self.table.id,
			'status': 'P',
			'items': [
				{'menu_item': self.soup.id, 'quantity': 2},
			]
		}

		serializer = OrderSerializer(data=data)
		self.assertTrue(serializer.is_valid(), serializer.errors)
		order = serializer.save()

		# After saving, inventory should be reduced by amount_needed * quantity (0.5 * 2 = 1.0)
		self.tomato.refresh_from_db()
		self.assertEqual(self.tomato.quantity, Decimal('9.00'))

		# Order total should be price * quantity = 5.00 * 2 = 10.00
		order.refresh_from_db()
		self.assertEqual(order.total_amount, Decimal('10.00'))
