from rest_framework import viewsets
from .models import MenuItem, Order, RestaurantTable
from .serializers import MenuItemSerializer, OrderSerializer

class MenuViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = OrderSerializer

    # Expert Logic: Calculate total price when placing order
    def perform_create(self, serializer):
        # Nested serializer now creates OrderItems and signals will update totals
        serializer.save()
