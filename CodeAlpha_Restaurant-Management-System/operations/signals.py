from django.db import models
from django.db.models import Sum, F
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import OrderItem, Recipe

@receiver(post_save, sender=OrderItem)
def reduce_inventory(sender, instance, created, **kwargs):
    if created:
        # 1. Find the recipes associated with the MenuItem ordered
        recipes = Recipe.objects.filter(menu_item=instance.menu_item)
        
        for recipe in recipes:
            ingredient = recipe.ingredient
            # 2. Subtract: (amount needed per item * quantity ordered)
            reduction_amount = recipe.amount_needed * instance.quantity
            
            # 3. Update the inventory
            ingredient.quantity -= reduction_amount
            ingredient.save()
            
            # 4. Optional: Print a warning in the console if stock is low
            if ingredient.quantity <= ingredient.min_stock_limit:
                print(f"⚠️ ALERT: {ingredient.name} is low on stock!")

@receiver([post_save, post_delete], sender=OrderItem)
def update_order_total(sender, instance, **kwargs):
    order = instance.order
    # Calculate the sum: (Quantity * Price of Menu Item)
    total = order.items.aggregate(
        total_sum=Sum(models.F('quantity') * models.F('menu_item__price'))
    )['total_sum'] or 0
    
    order.total_amount = total
    order.save()


@receiver(post_delete, sender=OrderItem)
def restore_inventory(sender, instance, **kwargs):
    # 1. Find the recipes associated with the item being deleted
    recipes = Recipe.objects.filter(menu_item=instance.menu_item)
    
    for recipe in recipes:
        ingredient = recipe.ingredient
        # 2. Add back: (amount per item * quantity deleted)
        return_amount = recipe.amount_needed * instance.quantity
        
        # 3. Update the inventory
        ingredient.quantity += return_amount
        ingredient.save()
        print(f"🔄 RESTOCKED: {ingredient.name} (+{return_amount} {ingredient.unit})")