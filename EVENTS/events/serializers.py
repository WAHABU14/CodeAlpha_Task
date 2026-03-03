from rest_framework import serializers
from .models import Event, Registration
from django.contrib.auth import get_user_model

User = get_user_model()


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['id', 'title', 'description', 'location', 'start_time', 'end_time', 'capacity']


class RegistrationSerializer(serializers.ModelSerializer):
    event = EventSerializer(read_only=True)
    event_id = serializers.PrimaryKeyRelatedField(queryset=Event.objects.all(), source='event', write_only=True)

    class Meta:
        model = Registration
        fields = ['id', 'user', 'event', 'event_id', 'status', 'created_at']
        read_only_fields = ['id', 'user', 'event', 'status', 'created_at']
