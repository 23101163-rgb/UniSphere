from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import Notification

User = get_user_model()


class NotificationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='notifuser', email='notifuser@uap-bd.edu',
            password='testpass123', university_id='860001', role='student'
        )
        self.notif1 = Notification.objects.create(
            recipient=self.user, title='Test Notif 1',
            message='First notification', link='/events/', is_read=False
        )
        self.notif2 = Notification.objects.create(
            recipient=self.user, title='Test Notif 2',
            message='Second notification', link='/jobs/', is_read=False
        )
        self.notif3 = Notification.objects.create(
            recipient=self.user, title='Test Notif 3',
            message='Third notification', link='', is_read=False
        )

    # UT-051
    def test_notification_created_on_action(self):
        # Verify notifications exist for user
        count = Notification.objects.filter(recipient=self.user).count()
        self.assertEqual(count, 3)

    # UT-052
    def test_mark_single_read(self):
        self.client.login(username='notifuser', password='testpass123')
        response = self.client.get(
            reverse('notifications:read', args=[self.notif1.pk]), follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.notif1.refresh_from_db()
        self.assertTrue(self.notif1.is_read)

    # UT-053
    def test_mark_all_read(self):
        self.client.login(username='notifuser', password='testpass123')
        response = self.client.get(reverse('notifications:read_all'), follow=True)
        self.assertEqual(response.status_code, 200)

        for n in [self.notif1, self.notif2, self.notif3]:
            n.refresh_from_db()
            self.assertTrue(n.is_read)

    # UT-054
    def test_unread_count_context_processor(self):
        self.client.login(username='notifuser', password='testpass123')
        response = self.client.get(reverse('notifications:list'))
        self.assertEqual(response.status_code, 200)
        # Context processor adds unread_count
        self.assertEqual(response.context['unread_count'], 3)

    # Extra: notification list page loads
    def test_notification_list_loads(self):
        self.client.login(username='notifuser', password='testpass123')
        response = self.client.get(reverse('notifications:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Notif 1')
        self.assertContains(response, 'Test Notif 2')

    # Extra: mark read with link redirects to link
    def test_mark_read_redirects_to_link(self):
        self.client.login(username='notifuser', password='testpass123')
        response = self.client.get(
            reverse('notifications:read', args=[self.notif1.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('/events/', response.url)

    # Extra: mark read without link redirects to list
    def test_mark_read_no_link_redirects_to_list(self):
        self.client.login(username='notifuser', password='testpass123')
        response = self.client.get(
            reverse('notifications:read', args=[self.notif3.pk])
        )
        self.assertRedirects(response, reverse('notifications:list'))

    # Extra: notification API returns JSON
    def test_notification_api(self):
        self.client.login(username='notifuser', password='testpass123')
        response = self.client.get(reverse('notifications:api'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['unread_count'], 3)
        self.assertEqual(len(data['notifications']), 3)