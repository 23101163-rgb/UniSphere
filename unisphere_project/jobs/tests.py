from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date, timedelta

from .models import JobListing, JobBookmark, JobApplication
from notifications.models import Notification

User = get_user_model()


class JobTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin1',
            email='admin1@uap-bd.edu',
            password='testpass123',
            university_id='900001',
            role='admin'
        )
        self.student = User.objects.create_user(
            username='student1',
            email='student1@uap-bd.edu',
            password='testpass123',
            university_id='900002',
            role='student'
        )
        self.poster = User.objects.create_user(
            username='poster1',
            email='poster1@uap-bd.edu',
            password='testpass123',
            university_id='900003',
            role='alumni'
        )

        self.job = JobListing.objects.create(
            title='Software Engineer',
            company_name='ABC Tech',
            job_type='job',
            description='Job description',
            required_skills='Python, Django',
            eligibility='CSE students',
            salary_range='20k-30k',
            application_deadline=date.today() + timedelta(days=7),
            application_link='https://example.com/apply',
            posted_by=self.poster,
            is_verified=True
        )

    def test_job_list_loads_for_logged_in_user(self):
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(reverse('jobs:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Software Engineer')

    def test_job_create_by_student(self):
        self.client.login(username='student1', password='testpass123')
        response = self.client.post(reverse('jobs:create'), {
            'title': 'Backend Intern',
            'company_name': 'XYZ Ltd',
            'job_type': 'internship',
            'description': 'Internship desc',
            'required_skills': 'Python',
            'eligibility': 'Student',
            'salary_range': '10k',
            'application_deadline': (date.today() + timedelta(days=10)).isoformat(),
            'application_link': 'https://example.com/intern'
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(JobListing.objects.filter(title='Backend Intern').exists())
        created_job = JobListing.objects.get(title='Backend Intern')
        self.assertFalse(created_job.is_verified)

    def test_job_verify_by_admin(self):
        self.job.is_verified = False
        self.job.save()

        self.client.login(username='admin1', password='testpass123')
        response = self.client.get(reverse('jobs:verify', args=[self.job.pk]), follow=True)

        self.job.refresh_from_db()
        self.assertTrue(self.job.is_verified)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.poster,
                title='Job Verified'
            ).exists()
        )

    def test_job_verify_denied_for_student(self):
        self.job.is_verified = False
        self.job.save()

        self.client.login(username='student1', password='testpass123')
        response = self.client.get(reverse('jobs:verify', args=[self.job.pk]), follow=True)

        self.job.refresh_from_db()
        self.assertFalse(self.job.is_verified)
        self.assertContains(response, 'Access denied.')

    def test_job_bookmark_toggle(self):
        self.client.login(username='student1', password='testpass123')

        self.client.get(reverse('jobs:bookmark', args=[self.job.pk]))
        self.assertTrue(JobBookmark.objects.filter(user=self.student, job=self.job).exists())

        self.client.get(reverse('jobs:bookmark', args=[self.job.pk]))
        self.assertFalse(JobBookmark.objects.filter(user=self.student, job=self.job).exists())

    def test_job_apply_creates_application_and_notifications(self):
        self.client.login(username='student1', password='testpass123')

        response = self.client.post(reverse('jobs:apply', args=[self.job.pk]), {
            'full_name': 'Student One',
            'email': 'student1@uap-bd.edu',
            'phone': '01700000000',
            'cover_letter': 'I am interested.',
            'cv_link': 'https://example.com/cv'
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(JobApplication.objects.filter(job=self.job, applicant=self.student).exists())
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.student,
                title='Job Application Submitted'
            ).exists()
        )
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.poster,
                title='New Job Application'
            ).exists()
        )

    def test_duplicate_job_apply_not_allowed(self):
        JobApplication.objects.create(
            job=self.job,
            applicant=self.student,
            full_name='Student One',
            email='student1@uap-bd.edu',
            phone='01700000000',
            cover_letter='Test',
            cv_link='https://example.com/cv'
        )

        self.client.login(username='student1', password='testpass123')
        response = self.client.get(reverse('jobs:apply', args=[self.job.pk]), follow=True)

        self.assertEqual(JobApplication.objects.filter(job=self.job, applicant=self.student).count(), 1)
        self.assertContains(response, 'already applied')
