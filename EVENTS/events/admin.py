from django.contrib import admin
from .models import Event, Registration


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'start_time', 'end_time', 'capacity')
    search_fields = ('title', 'description')


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'event', 'status', 'created_at')
    list_filter = ('status',)
