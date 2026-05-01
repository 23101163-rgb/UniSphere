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

    SEMESTER_CHOICES = [
        (f'{i}.{j}', f'Semester {i}.{j}')
        for i in range(1, 5)
        for j in range(1, 3)
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    university_id = models.CharField(max_length=20, unique=True, blank=True)
    department = models.CharField(max_length=100, default='CSE')

    profile_picture = models.ImageField(upload_to='uploads/profiles/', blank=True, null=True)
    bio = models.TextField(blank=True)
    phone = models.CharField(max_length=15, blank=True)

    semester = models.CharField(max_length=20, blank=True)
    # Legacy/single-course field kept for old data and old features.
    # New multi-course teacher assignments are stored in TeacherCourseAssignment.
    teacher_course_name = models.CharField(
        max_length=200,
        blank=True,
        help_text='Legacy assigned course for teacher material approval'
    )
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
    # Legacy/single-club fields kept for old data and old screens.
    # New multi-club membership is stored in ClubMembership.
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

    def get_authorized_club_names(self):
        """Return all clubs this user is verified/authorized to post for.

        This keeps the old single-club fields working and also supports the
        new multi-club membership table.
        """
        clubs = set()

        if self.is_club_member and self.is_club_verified and self.club_name:
            clubs.add(self.club_name)

        if self.pk:
            clubs.update(
                self.club_memberships.filter(
                    is_verified=True,
                    authorized_to_post=True
                ).values_list('club_name', flat=True)
            )

        return sorted(clubs)

    def get_club_names_for_profile(self):
        """Return selected clubs, including pending/unverified memberships."""
        clubs = set()
        if self.is_club_member and self.club_name:
            clubs.add(self.club_name)
        if self.pk:
            clubs.update(self.club_memberships.values_list('club_name', flat=True))
        return sorted(clubs)

    def can_post_for_club(self, club_name):
        if self.is_admin_user() or self.is_teacher():
            return True
        return club_name in self.get_authorized_club_names()

    # 🔥 TEACHER COURSE HELPERS
    def get_teacher_course_assignments(self):
        """Return [(semester, course_name), ...] for teacher approval checks."""
        assignments = []

        if self.pk:
            assignments.extend(
                list(
                    self.teacher_courses.values_list('semester', 'course_name')
                )
            )

        if not assignments and self.teacher_course_name:
            # Legacy field has no semester. Use it only when no new assignment exists.
            assignments.append(('', self.teacher_course_name.strip().upper()))

        seen = set()
        unique_assignments = []
        for semester, course_name in assignments:
            semester = (semester or '').strip()
            course_name = (course_name or '').strip().upper()
            key = (semester, course_name)
            if course_name and key not in seen:
                seen.add(key)
                unique_assignments.append(key)
        return unique_assignments

    def get_assigned_course_names(self):
        return sorted({course for _, course in self.get_teacher_course_assignments() if course})

    def can_approve_course(self, course_name, semester=None):
        if self.is_admin_user():
            return True
        if not self.is_teacher():
            return False

        course_name = (course_name or '').strip().upper()
        semester = (semester or '').strip()

        for assigned_semester, assigned_course in self.get_teacher_course_assignments():
            if assigned_course != course_name:
                continue
            # Legacy teacher_course_name has assigned_semester == '' and can approve
            # that course in any semester. New assignments match course + semester.
            if not assigned_semester or not semester or assigned_semester == semester:
                return True
        return False

    # 🔥 HELPER FOR AUTO UNIVERSITY ID
    @staticmethod
    def generate_unique_university_id():
        while True:
            new_id = str(random.randint(100000, 999999))
            if not User.objects.filter(university_id=new_id).exists():
                return new_id

    # 🔥 SAFETY + AUTO UNIVERSITY ID + CLUB VERIFICATION RESET
    def save(self, *args, **kwargs):
        if self.role == 'teacher' and self.teacher_course_name:
            self.teacher_course_name = self.teacher_course_name.strip().upper()
        elif self.role != 'teacher':
            self.teacher_course_name = ''

        if not self.is_club_member:
            self.club_name = ''
            self.club_position = ''
            self.is_club_verified = False

        # Reset verification if legacy club info changed
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


class ClubMembership(models.Model):
    """Multiple-club permission support without removing old User club fields."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='club_memberships'
    )
    club_name = models.CharField(max_length=100, choices=User.CLUB_CHOICES)
    club_position = models.CharField(max_length=50, choices=User.CLUB_POSITION_CHOICES, blank=True)
    is_verified = models.BooleanField(default=False)
    authorized_to_post = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'club_name')
        ordering = ['club_name']

    def __str__(self):
        return f'{self.user.get_full_name() or self.user.username} - {self.get_club_name_display()}'


class TeacherCourseAssignment(models.Model):
    """One teacher can be assigned to multiple courses in different semesters."""

    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='teacher_courses',
        limit_choices_to={'role': 'teacher'}
    )
    semester = models.CharField(max_length=10, choices=User.SEMESTER_CHOICES)
    course_name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('teacher', 'semester', 'course_name')
        ordering = ['semester', 'course_name']

    def save(self, *args, **kwargs):
        if self.course_name:
            self.course_name = self.course_name.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.teacher.get_full_name() or self.teacher.username} - {self.semester} - {self.course_name}'
