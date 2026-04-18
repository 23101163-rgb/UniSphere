from django.test import TestCase
from django.urls import reverse
from .models import User


class AccountTests(TestCase):
    def test_user_registration_with_valid_uap_email(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': 'testuser',
            'email': 'test@uap-bd.edu',
            'university_id': '23101111',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'student',
            'password1': 'StrongPass123',
            'password2': 'StrongPass123',
        })

        self.assertEqual(User.objects.count(), 1)
        self.assertRedirects(response, reverse('accounts:dashboard'))

    def test_registration_with_invalid_email_domain(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': 'baduser',
            'email': 'bad@gmail.com',
            'university_id': '23101112',
            'first_name': 'Bad',
            'last_name': 'User',
            'role': 'student',
            'password1': 'StrongPass123',
            'password2': 'StrongPass123',
        })

        self.assertEqual(User.objects.count(), 0)
        self.assertContains(response, 'Please use your university email')

    def test_duplicate_university_id_not_allowed(self):
        User.objects.create_user(
            username='existing',
            email='existing@uap-bd.edu',
            university_id='23101113',
            password='StrongPass123',
            role='student'
        )

        response = self.client.post(reverse('accounts:register'), {
            'username': 'newuser',
            'email': 'new@uap-bd.edu',
            'university_id': '23101113',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'student',
            'password1': 'StrongPass123',
            'password2': 'StrongPass123',
        })

        self.assertContains(response, 'This university ID is already registered.')

    def test_valid_login(self):
        user = User.objects.create_user(
            username='loginuser',
            email='login@uap-bd.edu',
            university_id='23101114',
            password='StrongPass123',
            role='student'
        )

        response = self.client.post(reverse('accounts:login'), {
            'username': 'loginuser',
            'password': 'StrongPass123'
        })

        self.assertRedirects(response, reverse('accounts:dashboard'))

    def test_invalid_login(self):
        User.objects.create_user(
            username='wronglogin',
            email='wrong@uap-bd.edu',
            university_id='23101115',
            password='StrongPass123',
            role='student'
        )

        response = self.client.post(reverse('accounts:login'), {
            'username': 'wronglogin',
            'password': 'WrongPass999'
        })

        self.assertContains(response, 'Wrong username/email or password.')