from django.urls import path
from . import views

urlpatterns = [
    path('events/', views.EventListView.as_view(), name='event-list'),
    path('events/<int:pk>/', views.EventDetailView.as_view(), name='event-detail'),
    path('events/<int:pk>/register/', views.register_for_event, name='event-register'),
    path('registrations/', views.UserRegistrationsView.as_view(), name='user-registrations'),
    path('registrations/<int:pk>/cancel/', views.cancel_registration, name='registration-cancel'),
]
