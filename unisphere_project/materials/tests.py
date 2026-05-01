from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from accounts.models import TeacherCourseAssignment
from .models import StudyMaterial, MaterialRating
from notifications.models import Notification

User = get_user_model()


class MaterialTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username='teacher2',
            email='teacher2@uap-bd.edu',
            password='testpass123',
            university_id='920001',
            role='teacher',
            teacher_course_name='CSE221'
        )

        self.student = User.objects.create_user(
            username='student3',
            email='student3@uap-bd.edu',
            password='testpass123',
            university_id='920002',
            role='student'
        )

        # Teacher assigned courses for approval tests
        TeacherCourseAssignment.objects.create(
            teacher=self.teacher,
            semester='2.1',
            course_name='CSE221'
        )

        TeacherCourseAssignment.objects.create(
            teacher=self.teacher,
            semester='2.2',
            course_name='CSE230'
        )

        TeacherCourseAssignment.objects.create(
            teacher=self.teacher,
            semester='3.1',
            course_name='CSE240'
        )

        self.test_file = SimpleUploadedFile(
            'test.pdf',
            b'%PDF-1.4 test pdf content',
            content_type='application/pdf'
        )

        self.material = StudyMaterial.objects.create(
            title='Data Structures Notes',
            description='Important notes',
            course_name='CSE221',
            semester='2.1',
            topic='Stack and Queue',
            tags='data structure, stack',
            file=self.test_file,
            uploaded_by=self.teacher,
            is_approved=True
        )

    def test_material_semesters_page_loads(self):
        self.client.login(username='student3', password='testpass123')

        response = self.client.get(reverse('materials:semesters'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Semester 2.1')

    def test_student_upload_material_pending(self):
        self.client.login(username='student3', password='testpass123')

        upload_file = SimpleUploadedFile(
            'upload.pdf',
            b'%PDF-1.4 upload content',
            content_type='application/pdf'
        )

        response = self.client.post(reverse('materials:create'), {
            'title': 'New Notes',
            'description': 'Some desc',
            'course_name': 'CSE220',
            'semester': '2.1',
            'topic': 'Trees',
            'tags': 'tree, bst',
            'file': upload_file
        }, follow=True)

        self.assertEqual(response.status_code, 200)

        material = StudyMaterial.objects.get(title='New Notes')
        self.assertFalse(material.is_approved)

    def test_teacher_upload_material_auto_approved(self):
        self.client.login(username='teacher2', password='testpass123')

        upload_file = SimpleUploadedFile(
            'teacher.pdf',
            b'%PDF-1.4 teacher content',
            content_type='application/pdf'
        )

        response = self.client.post(reverse('materials:create'), {
            'title': 'Teacher Notes',
            'description': 'Teacher desc',
            'course_name': 'CSE230',
            'semester': '2.2',
            'topic': 'Graphs',
            'tags': 'graph',
            'file': upload_file
        }, follow=True)

        self.assertEqual(response.status_code, 200)

        material = StudyMaterial.objects.get(title='Teacher Notes')
        self.assertTrue(material.is_approved)

    def test_material_download_increases_count_and_creates_notifications(self):
        self.client.login(username='student3', password='testpass123')

        response = self.client.get(
            reverse('materials:download', args=[self.material.pk])
        )

        self.assertEqual(response.status_code, 200)

        self.material.refresh_from_db()
        self.assertEqual(self.material.download_count, 1)

        self.assertTrue(
            Notification.objects.filter(
                recipient=self.student,
                title='Material Downloaded'
            ).exists()
        )

        self.assertTrue(
            Notification.objects.filter(
                recipient=self.teacher,
                title='Material Downloaded'
            ).exists()
        )

    def test_material_approve_creates_notification(self):
        upload_file = SimpleUploadedFile(
            'pending.pdf',
            b'%PDF-1.4 pending content',
            content_type='application/pdf'
        )

        pending_material = StudyMaterial.objects.create(
            title='Pending Notes',
            description='Pending desc',
            course_name='CSE240',
            semester='3.1',
            topic='OS',
            tags='os',
            file=upload_file,
            uploaded_by=self.student,
            is_approved=False
        )

        self.client.login(username='teacher2', password='testpass123')

        response = self.client.get(
            reverse('materials:approve', args=[pending_material.pk]),
            follow=True
        )

        self.assertEqual(response.status_code, 200)

        pending_material.refresh_from_db()
        self.assertTrue(pending_material.is_approved)

        self.assertTrue(
            Notification.objects.filter(
                recipient=self.student,
                title='Material Approved'
            ).exists()
        )

    def test_submit_rating(self):
        self.client.login(username='student3', password='testpass123')

        response = self.client.post(reverse('materials:detail', args=[self.material.pk]), {
            'score': 5,
            'review': 'Very helpful'
        }, follow=True)

        self.assertEqual(response.status_code, 200)

        self.assertTrue(
            MaterialRating.objects.filter(
                material=self.material,
                user=self.student
            ).exists()
        )

    def test_course_resources_page_loads(self):
        self.client.login(username='student3', password='testpass123')

        response = self.client.get(
            reverse('materials:course_materials', args=['2.1', 'CSE221'])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Data Structures Notes')