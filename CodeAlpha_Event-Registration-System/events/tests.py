from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from events.models import Event, Registration
from django.urls import reverse
from datetime import datetime, timedelta
from django.utils import timezone


class EventAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        User = get_user_model()
        self.user = User.objects.create_user(username='tester', password='pass')

        now = timezone.now()
        self.event = Event.objects.create(
            title='Test Event',
            description='Desc',
            start_time=now + timedelta(days=1),
            end_time=now + timedelta(days=1, hours=2),
        )

    def test_list_events(self):
        res = self.client.get(reverse('event-list'))
        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(res.data) >= 1)

    def test_register_requires_auth(self):
        url = reverse('event-register', args=[self.event.id])
        res = self.client.post(url)
        self.assertEqual(res.status_code, 401)

    def test_register_and_cancel(self):
        self.client.force_authenticate(user=self.user)
        reg_url = reverse('event-register', args=[self.event.id])
        res = self.client.post(reg_url)
        self.assertEqual(res.status_code, 201)
        reg_id = res.data['id']

        # list registrations
        res = self.client.get(reverse('user-registrations'))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)

        # cancel
        cancel_url = reverse('registration-cancel', args=[reg_id])
        res = self.client.post(cancel_url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(Registration.objects.get(id=reg_id).status, 'cancelled')
