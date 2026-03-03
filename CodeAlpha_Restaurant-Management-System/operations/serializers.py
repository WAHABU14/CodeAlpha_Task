from rest_framework import serializers
from .models import MenuItem, Order, OrderItem, RestaurantTable, Reservation


class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'price', 'category']


class OrderItemSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.ReadOnlyField(source='menu_item.name')

    class Meta:
        model = OrderItem
        # allow menu_item and quantity to be written when nested under Order
        fields = ['id', 'menu_item', 'menu_item_name', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    # Make items writable so clients can create an Order with items in one request
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ['id', 'table', 'status', 'total_amount', 'items', 'created_at']
        read_only_fields = ('total_amount', 'created_at')

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        # create the Order first
        order = Order.objects.create(**validated_data)

        # create related OrderItem objects
        for item_data in items_data:
            # item_data['menu_item'] will be a model instance (PrimaryKeyRelatedField behavior)
            OrderItem.objects.create(order=order, **item_data)

        # At this point signals will recalculate the order total and reduce inventory
        # Refresh from db to get updated total_amount
        order.refresh_from_db()
        return order

    def update(self, instance, validated_data):
        # Support updating order-level fields and replacing items if provided
        items_data = validated_data.pop('items', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is not None:
            # simple strategy: delete existing items and recreate
            instance.items.all().delete()
            for item_data in items_data:
                OrderItem.objects.create(order=instance, **item_data)

        instance.refresh_from_db()
        return instance
