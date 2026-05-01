from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import Complaint
from notifications.models import Notification

User = get_user_model()


class ComplaintTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='compadmin', email='compadmin@uap-bd.edu',
            password='testpass123', university_id='810001', role='admin'
        )
        self.student = User.objects.create_user(
            username='compstudent', email='compstudent@uap-bd.edu',
            password='testpass123', university_id='810002', role='student'
        )
        self.teacher = User.objects.create_user(
            username='compteacher', email='compteacher@uap-bd.edu',
            password='testpass123', university_id='810003', role='teacher'
        )

    # UT-035
    def test_complaint_submit(self):
        self.client.login(username='compstudent', password='testpass123')
        response = self.client.post(reverse('complaints:submit'), {
            'target_type': 'admin',
            'subject': 'Lab AC broken',
            'description': 'AC in Lab 5 is not working',
            'category': 'infrastructure',
            'is_anonymous': False,
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        complaint = Complaint.objects.get(subject='Lab AC broken')
        self.assertEqual(complaint.status, 'submitted')
        self.assertEqual(complaint.submitted_by, self.student)

    # UT-036
    def test_anonymous_complaint_hides_identity(self):
        self.client.login(username='compstudent', password='testpass123')
        self.client.post(reverse('complaints:submit'), {
            'target_type': 'admin',
            'subject': 'Anonymous Issue',
            'description': 'Something private',
            'category': 'harassment',
            'is_anonymous': True,
        })
        complaint = Complaint.objects.get(subject='Anonymous Issue')
        self.assertTrue(complaint.is_anonymous)

    # UT-037
    def test_admin_respond(self):
        complaint = Complaint.objects.create(
            subject='Test Complaint', description='Desc',
            category='academic', submitted_by=self.student,
            target_type='admin'
        )
        self.client.login(username='compadmin', password='testpass123')
        response = self.client.post(reverse('complaints:respond', args=[complaint.pk]), {
            'status': 'in_review',
            'admin_response': 'We are looking into this.',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        complaint.refresh_from_db()
        self.assertEqual(complaint.status, 'in_review')
        self.assertEqual(complaint.admin_response, 'We are looking into this.')
        # Notification sent to submitter
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.student,
                title__startswith='Complaint Update'
            ).exists()
        )

    # UT-038
    def test_teacher_complaint_manage(self):
        Complaint.objects.create(
            subject='Teacher Complaint', description='Issue with grading',
            category='academic', submitted_by=self.student,
            target_type='teacher', target_teacher=self.teacher
        )
        self.client.login(username='compteacher', password='testpass123')
        response = self.client.get(reverse('complaints:teacher_manage'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Teacher Complaint')

    # UT-039
    def test_status_update(self):
        complaint = Complaint.objects.create(
            subject='Status Test', description='Desc',
            category='other', submitted_by=self.student,
            target_type='admin'
        )
        self.client.login(username='compadmin', password='testpass123')

        # Update to in_review
        self.client.post(reverse('complaints:respond', args=[complaint.pk]), {
            'status': 'in_review',
            'admin_response': 'Reviewing now.',
        })
        complaint.refresh_from_db()
        self.assertEqual(complaint.status, 'in_review')

        # Update to resolved
        self.client.post(reverse('complaints:respond', args=[complaint.pk]), {
            'status': 'resolved',
            'admin_response': 'Issue fixed.',
        })
        complaint.refresh_from_db()
        self.assertEqual(complaint.status, 'resolved')

    # Extra: admin manage page access control
    def test_student_cannot_access_complaint_manage(self):
        self.client.login(username='compstudent', password='testpass123')
        response = self.client.get(reverse('complaints:manage'), follow=True)
        self.assertContains(response, 'Access denied')

    # Extra: complaint submit notifies admin
    def test_complaint_submit_notifies_admin(self):
        self.client.login(username='compstudent', password='testpass123')
        self.client.post(reverse('complaints:submit'), {
            'target_type': 'admin',
            'subject': 'Notify Admin Test',
            'description': 'Test',
            'category': 'academic',
            'is_anonymous': False,
        })
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.admin,
                title='New Complaint Received'
            ).exists()
        )

    # Extra: teacher-targeted complaint notifies teacher
    def test_teacher_complaint_notifies_teacher(self):
        self.client.login(username='compstudent', password='testpass123')
        self.client.post(reverse('complaints:submit'), {
            'target_type': 'teacher',
            'target_teacher': self.teacher.pk,
            'subject': 'Grading Issue',
            'description': 'Wrong marks',
            'category': 'academic',
            'is_anonymous': False,
        })
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.teacher,
                title='New Complaint Received'
            ).exists()
        )
