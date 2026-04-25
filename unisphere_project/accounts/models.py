from django.contrib.auth.models import AbstractUser
from django.db import models
import random


class User(AbstractUser):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('alumni', 'Alumni'),
        ('admin', 'Admin'),
    ]

    CLUB_CHOICES = [
        ('', 'Select Club'),
        ('uap_programming_contest_club', 'UAP Programming Contest Club'),
        ('software_hardware_club', 'Software and Hardware Club'),
        ('cyber_security_club', 'Cyber Security Club, CSE, UAP'),
        ('career_development_club', 'Career Development Club'),
        ('math_club', 'Math Club'),
        ('research_publication_units', 'Research and Publication Units'),
        ('robotics_club', 'Robotics Club'),
        ('photography_club', 'Photography Club'),
        ('sports_club', 'Sports Club'),
        ('cultural_club', 'Cultural Club'),
    ]

    CLUB_POSITION_CHOICES = [
        ('', 'Select Position'),
        ('member', 'Member'),
        ('executive_member', 'Executive Member'),
        ('senior_executive', 'Senior Executive'),
        ('assistant_secretary', 'Assistant Secretary'),
        ('secretary', 'Secretary'),
        ('vice_president', 'Vice President'),
        ('president', 'President'),
        ('coordinator', 'Coordinator'),
        ('organizer', 'Organizer'),
        ('volunteer', 'Volunteer'),
        ('other', 'Other'),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    university_id = models.CharField(max_length=20, unique=True, blank=True)
    department = models.CharField(max_length=100, default='CSE')

    profile_picture = models.ImageField(upload_to='uploads/profiles/', blank=True, null=True)
    bio = models.TextField(blank=True)
    phone = models.CharField(max_length=15, blank=True)

    semester = models.CharField(max_length=20, blank=True)
    research_interests = models.TextField(blank=True)
    expertise = models.TextField(blank=True)

    graduation_year = models.IntegerField(null=True, blank=True)
    company = models.CharField(max_length=200, blank=True)
    designation = models.CharField(max_length=200, blank=True)

    is_mentor_available = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)

    # 🔥 CLUB SYSTEM
    is_club_member = models.BooleanField(default=False)
    is_club_verified = models.BooleanField(default=False)
    club_name = models.CharField(max_length=100, choices=CLUB_CHOICES, blank=True)
    club_position = models.CharField(max_length=50, choices=CLUB_POSITION_CHOICES, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"

    # 🔹 ROLE HELPERS
    def is_student(self):
        return self.role == 'student'

    def is_teacher(self):
        return self.role == 'teacher'

    def is_alumni(self):
        return self.role == 'alumni'

    def is_admin_user(self):
        return self.role == 'admin'

    # 🔥 CLUB DISPLAY HELPERS
    def get_club_display(self):
        return dict(self.CLUB_CHOICES).get(self.club_name, '')

    def get_club_position_display(self):
        return dict(self.CLUB_POSITION_CHOICES).get(self.club_position, '')

    # 🔥 HELPER FOR AUTO UNIVERSITY ID
    @staticmethod
    def generate_unique_university_id():
        while True:
            new_id = str(random.randint(100000, 999999))
            if not User.objects.filter(university_id=new_id).exists():
                return new_id

    # 🔥 SAFETY + AUTO UNIVERSITY ID + CLUB VERIFICATION RESET
    def save(self, *args, **kwargs):
        if not self.is_club_member:
            self.club_name = ''
            self.club_position = ''
            self.is_club_verified = False

        # Reset verification if club info changed
        if self.pk:
            try:
                old = User.objects.get(pk=self.pk)
                if (old.club_name != self.club_name or
                    old.club_position != self.club_position or
                    old.is_club_member != self.is_club_member):
                    self.is_club_verified = False
            except User.DoesNotExist:
                pass

        if not self.university_id:
            self.university_id = self.generate_unique_university_id()

        super().save(*args, **kwargs)