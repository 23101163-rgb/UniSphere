from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import User
from .models import StudyMaterial, MaterialRating


class MaterialTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username='student1',
            email='student1@uap-bd.edu',
            university_id='23101121',
            password='StrongPass123',
            role='student'
        )

        self.teacher = User.objects.create_user(
            username='teacher1',
            email='teacher1@uap-bd.edu',
            university_id='23101122',
            password='StrongPass123',
            role='teacher'
        )

        self.alumni = User.objects.create_user(
            username='alumni1',
            email='alumni1@uap-bd.edu',
            university_id='23101123',
            password='StrongPass123',
            role='alumni'
        )

    def test_teacher_uploaded_material_auto_approved(self):
        self.client.login(username='teacher1', password='StrongPass123')

        file = SimpleUploadedFile("test.pdf", b"dummy file content", content_type="application/pdf")

        self.client.post(reverse('materials:create'), {
            'title': 'Teacher Material',
            'description': 'Test description',
            'course_name': 'CSE101',
            'semester': '1.1',
            'topic': 'Intro',
            'tags': 'python,test',
            'file': file,
        })

        material = StudyMaterial.objects.first()
        self.assertTrue(material.is_approved)

    def test_student_uploaded_material_needs_approval(self):
        self.client.login(username='student1', password='StrongPass123')

        file = SimpleUploadedFile("test.pdf", b"dummy file content", content_type="application/pdf")

        self.client.post(reverse('materials:create'), {
            'title': 'Student Material',
            'description': 'Test description',
            'course_name': 'CSE102',
            'semester': '1.1',
            'topic': 'Basics',
            'tags': 'notes',
            'file': file,
        })

        material = StudyMaterial.objects.first()
        self.assertFalse(material.is_approved)

    def test_alumni_uploaded_material_auto_approved(self):
        self.client.login(username='alumni1', password='StrongPass123')

        file = SimpleUploadedFile("test.pdf", b"dummy file content", content_type="application/pdf")

        self.client.post(reverse('materials:create'), {
            'title': 'Alumni Material',
            'description': 'Test description',
            'course_name': 'CSE103',
            'semester': '1.1',
            'topic': 'Advanced',
            'tags': 'alumni',
            'file': file,
        })

        material = StudyMaterial.objects.first()
        self.assertTrue(material.is_approved)

    def test_only_approved_materials_visible_in_list(self):
        StudyMaterial.objects.create(
            title='Approved Material',
            description='Desc',
            course_name='CSE104',
            semester='1.1',
            topic='Topic',
            tags='tag',
            file='uploads/materials/test.pdf',
            uploaded_by=self.teacher,
            is_approved=True
        )

        StudyMaterial.objects.create(
            title='Pending Material',
            description='Desc',
            course_name='CSE105',
            semester='1.1',
            topic='Topic',
            tags='tag',
            file='uploads/materials/test2.pdf',
            uploaded_by=self.student,
            is_approved=False
        )

        self.client.login(username='student1', password='StrongPass123')
        response = self.client.get(reverse('materials:list'))

        self.assertContains(response, 'Approved Material')
        self.assertNotContains(response, 'Pending Material')

    def test_download_count_increments(self):
        material = StudyMaterial.objects.create(
            title='Download Material',
            description='Desc',
            course_name='CSE106',
            semester='1.1',
            topic='Topic',
            tags='tag',
            file='uploads/materials/test.pdf',
            uploaded_by=self.teacher,
            is_approved=True
        )

        self.client.login(username='student1', password='StrongPass123')
        self.client.get(reverse('materials:download', args=[material.pk]))

        material.refresh_from_db()
        self.assertEqual(material.download_count, 1)

    def test_one_user_one_rating(self):
        material = StudyMaterial.objects.create(
            title='Rate Material',
            description='Desc',
            course_name='CSE107',
            semester='1.1',
            topic='Topic',
            tags='tag',
            file='uploads/materials/test.pdf',
            uploaded_by=self.teacher,
            is_approved=True
        )

        MaterialRating.objects.create(material=material, user=self.student, score=4)
        rating = MaterialRating.objects.filter(material=material, user=self.student)
        self.assertEqual(rating.count(), 1)

