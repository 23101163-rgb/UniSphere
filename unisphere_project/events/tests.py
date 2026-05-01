from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date, time, timedelta

from .models import Event, EventRegistration
from notifications.models import Notification

User = get_user_model()


class EventTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username='teacher1',
            email='teacher1@uap-bd.edu',
            password='testpass123',
            university_id='910001',
            role='teacher'
        )
        self.student = User.objects.create_user(
            username='student2',
            email='student2@uap-bd.edu',
            password='testpass123',
            university_id='910002',
            role='student',
            first_name='Test',
            last_name='Student',
            department='CSE',
        )
        self.club_student = User.objects.create_user(
            username='clubstudent',
            email='clubstudent@uap-bd.edu',
            password='testpass123',
            university_id='910003',
            role='student',
            is_club_member=True,
            club_name='robotics_club',
            club_position='member'
        )

        self.event = Event.objects.create(
            title='AI Workshop',
            description='Workshop on AI',
            event_type='workshop',
            organizer_category='club',
            club_name='robotics_club',
            date=date.today() + timedelta(days=2),
            time=time(10, 0),
            venue='Room 101',
            registration_link='https://example.com/event',
            created_by=self.teacher,
            is_approved=True
        )

    def test_event_list_loads(self):
        self.client.login(username='student2', password='testpass123')
        response = self.client.get(reverse('events:list'))
        self.assertEqual(response.status_code, 200)

    def test_teacher_can_create_event(self):
        self.client.login(username='teacher1', password='testpass123')
        response = self.client.post(reverse('events:create'), {
            'title': 'Career Talk',
            'description': 'A career session',
            'organizer_category': 'non_club',
            'club_name': '',
            'event_type': 'career',
            'date': (date.today() + timedelta(days=5)).isoformat(),
            'time': '11:00',
            'venue': 'Auditorium',
            'registration_link': 'https://example.com/talk'
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Event.objects.filter(title='Career Talk').exists())

    # FIXED: View allows all students to create, but normal student's event is NOT approved
    def test_normal_student_event_not_auto_approved(self):
        self.client.login(username='student2', password='testpass123')
        response = self.client.post(reverse('events:create'), {
            'title': 'Student Event',
            'description': 'Student created event',
            'organizer_category': 'non_club',
            'club_name': '',
            'event_type': 'seminar',
            'date': (date.today() + timedelta(days=5)).isoformat(),
            'time': '14:00',
            'venue': 'Classroom',
            'registration_link': ''
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        event = Event.objects.get(title='Student Event')
        self.assertFalse(event.is_approved)

    def test_club_member_student_can_create_club_event(self):
        self.client.login(username='clubstudent', password='testpass123')
        response = self.client.post(reverse('events:create'), {
            'title': 'Robotics Meetup',
            'description': 'Club meetup',
            'organizer_category': 'club',
            'club_name': 'math_club',  # should be overridden
            'event_type': 'training',
            'date': (date.today() + timedelta(days=4)).isoformat(),
            'time': '12:00',
            'venue': 'Lab',
            'registration_link': 'https://example.com/meetup'
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        event = Event.objects.get(title='Robotics Meetup')
        self.assertEqual(event.club_name, 'robotics_club')

    # FIXED: Registration requires POST with form data
    def test_student_register_event_creates_notification(self):
        self.client.login(username='student2', password='testpass123')
        response = self.client.post(reverse('events:register', args=[self.event.pk]), {
            'full_name': 'Test Student',
            'email': 'student2@uap-bd.edu',
            'phone': '01700000000',
            'department': 'CSE',
            'university_id': '910002',
            'note': '',
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(EventRegistration.objects.filter(event=self.event, user=self.student).exists())
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.student,
                title='Event Registration Successful'
            ).exists()
        )
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.teacher,
                title='New Event Registration'
            ).exists()
        )

    # FIXED: First register via POST, then cancel via GET
    def test_event_register_toggle_cancel(self):
        # Register first via POST
        self.client.login(username='student2', password='testpass123')
        self.client.post(reverse('events:register', args=[self.event.pk]), {
            'full_name': 'Test Student',
            'email': 'student2@uap-bd.edu',
            'phone': '01700000000',
            'department': 'CSE',
            'university_id': '910002',
            'note': '',
        })
        self.assertTrue(EventRegistration.objects.filter(event=self.event, user=self.student).exists())

        # Cancel via GET (view detects existing registration and deletes)
        response = self.client.get(reverse('events:register', args=[self.event.pk]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(EventRegistration.objects.filter(event=self.event, user=self.student).exists())

    def test_my_events_page(self):
        EventRegistration.objects.create(event=self.event, user=self.student)
        self.client.login(username='student2', password='testpass123')

        response = self.client.get(reverse('events:my_events'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AI Workshop')

    def test_event_participants_permission(self):
        EventRegistration.objects.create(event=self.event, user=self.student)

        self.client.login(username='teacher1', password='testpass123')
        response = self.client.get(reverse('events:participants', args=[self.event.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'student2')
