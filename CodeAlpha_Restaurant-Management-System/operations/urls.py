from django.urls import path, include
from rest_framework.routers import DefaultRouter
from operations import views
from . import views_admin


router = DefaultRouter()
router.register(r'menu', views.MenuViewSet)
router.register(r'orders', views.OrderViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    # Simple admin dashboard (not the Django admin)
    path('dashboard/', views_admin.InventoryListView.as_view(), name='dashboard-inventory'),
    path('dashboard/menu/', views_admin.MenuListView.as_view(), name='dashboard-menu'),
    path('dashboard/orders/', views_admin.OrdersListView.as_view(), name='dashboard-orders'),
]