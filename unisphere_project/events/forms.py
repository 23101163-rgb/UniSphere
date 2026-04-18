from django.db import models
from django.conf import settings
from django.utils import timezone


class Event(models.Model):
    TYPE_CHOICES = [
        ('seminar', 'Seminar'),
        ('workshop', 'Workshop'),
        ('hackathon', 'Hackathon'),
        ('competition', 'Competition'),
        ('training', 'Training'),
        ('career', 'Career Session'),
    ]

    ORGANIZER_CHOICES = [
        ('club', 'Club Event'),
        ('non_club', 'Non-Club Event'),
    ]

    CLUB_CHOICES = [
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

    title = models.CharField(max_length=300)
    description = models.TextField()
    event_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    organizer_category = models.CharField(max_length=20, choices=ORGANIZER_CHOICES, default='club')
    club_name = models.CharField(max_length=100, choices=CLUB_CHOICES, blank=True)
    date = models.DateField(db_index=True)
    time = models.TimeField()
    venue = models.CharField(max_length=300)
    registration_link = models.URLField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_events'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'time', '-created_at']

    def _str_(self):
        return self.title

    def get_event_status(self):
        today = timezone.localdate()
        if self.date > today:
            return 'upcoming'
        elif self.date == today:
            return 'ongoing'
        return 'ended'

    def registration_count(self):
        return self.registrations.count()


class EventRegistration(models.Model):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='registrations'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('event', 'user')
        ordering = ['-registered_at']

    def _str_(self):
        return f'{self.user.username} registered for {self.event.title}'