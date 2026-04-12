from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('alumni', 'Alumni'),
        ('admin', 'Admin'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    university_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100, default='CSE')
    profile_picture = models.ImageField(upload_to='uploads/profiles/', blank=True, null=True)
    bio = models.TextField(blank=True)
    phone = models.CharField(max_length=15, blank=True)
    semester = models.CharField(max_length=20, blank=True)  # For students
    research_interests = models.TextField(blank=True)
    expertise = models.TextField(blank=True)  # For teachers/alumni
    graduation_year = models.IntegerField(null=True, blank=True)  # For alumni
    company = models.CharField(max_length=200, blank=True)  # For alumni
    designation = models.CharField(max_length=200, blank=True)  # For alumni
    is_mentor_available = models.BooleanField(default=False)  # For teachers/alumni
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"

    def is_student(self):
        return self.role == 'student'
    def is_teacher(self):
        return self.role == 'teacher'
    def is_alumni(self):
        return self.role == 'alumni'

    def is_admin_user(self):
        return self.role == 'admin' or self.is_superuser
