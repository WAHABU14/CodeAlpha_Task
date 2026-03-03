from django.utils import timezone
from django.db import models
from django.core.exceptions import ValidationError

# 1. TABLES & RESERVATIONS
class RestaurantTable(models.Model):
    number = models.PositiveIntegerField(unique=True)
    capacity = models.PositiveIntegerField()
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"Table {self.number} ({self.capacity} seats)"

class Reservation(models.Model):
    table = models.ForeignKey(RestaurantTable, on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=100)
    booking_time = models.DateTimeField()
    number_of_guests = models.PositiveIntegerField()

    def clean(self):
        if self.number_of_guests > self.table.capacity:
            raise ValidationError("Guests exceed table capacity!")

# 2. MENU & INVENTORY
class InventoryItem(models.Model):
    name = models.CharField(max_length=100)
    quantity = models.DecimalField(max_digits=10, decimal_places=2) # e.g. 50.00
    unit = models.CharField(max_length=20) # kg, liters, pcs
    min_stock_limit = models.DecimalField(max_digits=10, decimal_places=2, default=5.0)

    def __str__(self):
        return f"{self.name} ({self.quantity} {self.unit})"
    
    @property
    def status_color(self):
        if self.quantity <= self.min_stock_limit:
            return "🔴 Critical"
        elif self.quantity <= self.min_stock_limit * 2:
            return "🟡 Low"
        return "🟢 Healthy"

class MenuItem(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50) # e.g. Appetizer, Main, Drink
    ingredients = models.ManyToManyField(InventoryItem, through='Recipe')

    def __str__(self):
        return self.name

class Recipe(models.Model):
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    amount_needed = models.DecimalField(max_digits=10, decimal_places=2)

# 3. ORDERS
class Order(models.Model):
    STATUS_CHOICES = [
        ('P', 'Pending'),
        ('C', 'Cooking'),
        ('S', 'Served'),
        ('D', 'Done/Paid'),
    ]
    table = models.ForeignKey(RestaurantTable, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P')
    created_at = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def clean(self):
        # 1. Check if the table is already occupied by an active order
        if self.table and not self.table.is_available:
            # If the order is NEW, but the table is TAKEN, block it.
            if not self.pk: # Only check for new orders
                raise ValidationError(f"Table {self.table.number} is currently occupied!")

        # 2. Check for Reservations within the next 30 minutes
        buffer_time = timezone.now() + timezone.timedelta(minutes=30)
        upcoming_reservation = Reservation.objects.filter(
            table=self.table,
            booking_time__range=(timezone.now(), buffer_time)
        ).exists()

        if upcoming_reservation:
            raise ValidationError(f"Table {self.table.number} is reserved for someone arriving soon!")

    def save(self, *args, **kwargs):
        self.full_clean() # This triggers the 'clean' method above
        
        # Auto-update table status: If order is placed, table is no longer available
        if self.status in ['P', 'C', 'S']:
            self.table.is_available = False
        else:
            self.table.is_available = True
            
        self.table.save()
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
