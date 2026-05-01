from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import ThesisResource, MentorshipRequest, ResearchGroup

User = get_user_model()


class ThesisTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username='thesisteacher', email='thesisteacher@uap-bd.edu',
            password='testpass123', university_id='820001', role='teacher',
            is_mentor_available=True, expertise='Machine Learning',
            research_interests='NLP, Computer Vision'
        )
        self.student = User.objects.create_user(
            username='thesisstudent', email='thesisstudent@uap-bd.edu',
            password='testpass123', university_id='820002', role='student'
        )

    # UT-040
    def test_thesis_create(self):
        self.client.login(username='thesisteacher', password='testpass123')
        response = self.client.post(reverse('thesis:create'), {
            'title': 'AI in Healthcare',
            'abstract': 'This thesis explores AI applications in healthcare.',
            'authors': 'Dr. Smith, John Doe',
            'year': 2025,
            'research_area': 'Artificial Intelligence',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ThesisResource.objects.filter(title='AI in Healthcare').exists())


    # UT-041 — FIXED
    def test_mentor_list(self):
        self.client.login(username='thesisstudent', password='testpass123')
        response = self.client.get(reverse('thesis:mentors'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Machine Learning')

    # UT-042
    def test_mentorship_request_lifecycle(self):
        self.client.login(username='thesisstudent', password='testpass123')

        # Send request
        response = self.client.post(
            reverse('thesis:send_request', args=[self.teacher.pk]), {
                'topic': 'NLP Research',
                'message': 'I want to work on NLP under your guidance.',
            }, follow=True
        )
        self.assertEqual(response.status_code, 200)
        mr = MentorshipRequest.objects.get(student=self.student, mentor=self.teacher)
        self.assertEqual(mr.status, 'pending')

        # Teacher accepts
        self.client.login(username='thesisteacher', password='testpass123')
        response = self.client.get(
            reverse('thesis:handle_request', args=[mr.pk, 'accepted']),
            follow=True
        )
        mr.refresh_from_db()
        self.assertEqual(mr.status, 'accepted')

    # Extra: thesis list search
    def test_thesis_list_search(self):
        ThesisResource.objects.create(
            title='Blockchain Security', abstract='Study on blockchain',
            authors='Alice', year=2024, research_area='Security',
            uploaded_by=self.teacher
        )
        self.client.login(username='thesisstudent', password='testpass123')
        response = self.client.get(reverse('thesis:list'), {'q': 'Blockchain'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Blockchain Security')

    # Extra: mentorship decline
    def test_mentorship_request_decline(self):
        self.client.login(username='thesisstudent', password='testpass123')
        self.client.post(
            reverse('thesis:send_request', args=[self.teacher.pk]), {
                'topic': 'CV Research', 'message': 'Please guide me.',
            }
        )
        mr = MentorshipRequest.objects.get(student=self.student)

        self.client.login(username='thesisteacher', password='testpass123')
        self.client.get(reverse('thesis:handle_request', args=[mr.pk, 'declined']))
        mr.refresh_from_db()
        self.assertEqual(mr.status, 'declined')
