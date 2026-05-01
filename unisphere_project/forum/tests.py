from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import Category, Thread, Reply, Vote
from notifications.models import Notification

User = get_user_model()


class ForumTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='forumuser1', email='forum1@uap-bd.edu',
            password='testpass123', university_id='800001', role='student'
        )
        self.user2 = User.objects.create_user(
            username='forumuser2', email='forum2@uap-bd.edu',
            password='testpass123', university_id='800002', role='student'
        )
        self.category = Category.objects.create(
            name='General Discussion', description='Talk about anything', slug='general'
        )
        self.thread = Thread.objects.create(
            title='Test Thread', content='This is test content',
            category=self.category, author=self.user1
        )

    # UT-028
    def test_thread_create(self):
        self.client.login(username='forumuser1', password='testpass123')
        response = self.client.post(reverse('forum:thread_create'), {
            'title': 'New Discussion',
            'content': 'Some content here',
            'category': self.category.pk,
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Thread.objects.filter(title='New Discussion').exists())

    # UT-029
    def test_reply_to_thread(self):
        self.client.login(username='forumuser2', password='testpass123')
        response = self.client.post(reverse('forum:thread_detail', args=[self.thread.pk]), {
            'content': 'This is a reply',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.thread.replies.count(), 1)

    # UT-030
    def test_nested_reply(self):
        parent_reply = Reply.objects.create(
            thread=self.thread, author=self.user1, content='Parent reply'
        )
        self.client.login(username='forumuser2', password='testpass123')
        response = self.client.post(reverse('forum:thread_detail', args=[self.thread.pk]), {
            'content': 'Child reply',
            'parent_id': parent_reply.pk,
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        child = Reply.objects.filter(parent=parent_reply)
        self.assertEqual(child.count(), 1)
        self.assertEqual(child.first().content, 'Child reply')

    # UT-031
    def test_upvote_toggle(self):
        self.client.login(username='forumuser2', password='testpass123')

        # First click — upvote
        self.client.get(reverse('forum:upvote', args=[self.thread.pk]))
        self.assertEqual(Vote.objects.filter(user=self.user2, thread=self.thread).count(), 1)

        # Second click — remove upvote
        self.client.get(reverse('forum:upvote', args=[self.thread.pk]))
        self.assertEqual(Vote.objects.filter(user=self.user2, thread=self.thread).count(), 0)

    # UT-032
    def test_search_threads(self):
        self.client.login(username='forumuser1', password='testpass123')
        response = self.client.get(reverse('forum:search'), {'q': 'Test Thread'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Thread')

    # UT-033
    def test_flag_content(self):
        self.client.login(username='forumuser2', password='testpass123')
        response = self.client.get(
            reverse('forum:flag', args=['thread', self.thread.pk]),
            HTTP_REFERER=reverse('forum:home')
        )
        self.thread.refresh_from_db()
        self.assertTrue(self.thread.is_flagged)

    # UT-034
    def test_category_page_loads(self):
        self.client.login(username='forumuser1', password='testpass123')
        response = self.client.get(reverse('forum:category', args=['general']))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Thread')

    # Extra: upvote notification
    def test_upvote_creates_notification(self):
        self.client.login(username='forumuser2', password='testpass123')
        self.client.get(reverse('forum:upvote', args=[self.thread.pk]))
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.user1,
                title='Someone Liked Your Post'
            ).exists()
        )

    # Extra: reply notification
    def test_reply_creates_notification(self):
        self.client.login(username='forumuser2', password='testpass123')
        self.client.post(reverse('forum:thread_detail', args=[self.thread.pk]), {
            'content': 'Nice post!',
        })
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.user1,
                title='New Comment on Your Post'
            ).exists()
        )

    # Extra: view count increments
    def test_view_count_increments(self):
        self.client.login(username='forumuser1', password='testpass123')
        old_count = self.thread.views_count
        self.client.get(reverse('forum:thread_detail', args=[self.thread.pk]))
        self.thread.refresh_from_db()
        self.assertEqual(self.thread.views_count, old_count + 1)
