from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404

from .models import Event, Registration
from .serializers import EventSerializer, RegistrationSerializer


class EventListView(generics.ListAPIView):
    queryset = Event.objects.all().order_by('start_time')
    serializer_class = EventSerializer
    permission_classes = [permissions.AllowAny]


class EventDetailView(generics.RetrieveAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.AllowAny]


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def register_for_event(request, pk):
    event = get_object_or_404(Event, pk=pk)
    user = request.user

    # Prevent duplicate registration
    reg, created = Registration.objects.get_or_create(user=user, event=event)
    if not created and reg.status == 'registered':
        return Response({'detail': 'Already registered'}, status=status.HTTP_400_BAD_REQUEST)

    reg.status = 'registered'
    reg.save()

    serializer = RegistrationSerializer(reg)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserRegistrationsView(generics.ListAPIView):
    serializer_class = RegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Registration.objects.filter(user=self.request.user).select_related('event')


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cancel_registration(request, pk):
    reg = get_object_or_404(Registration, pk=pk, user=request.user)
    if reg.status == 'cancelled':
        return Response({'detail': 'Already cancelled'}, status=status.HTTP_400_BAD_REQUEST)
    reg.status = 'cancelled'
    reg.save()
    return Response({'detail': 'Cancelled'})
