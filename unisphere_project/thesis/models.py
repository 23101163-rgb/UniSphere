from django.db import models
from django.conf import settings

class ThesisResource(models.Model):
    title = models.CharField(max_length=300)
    abstract = models.TextField()
    authors = models.CharField(max_length=500)
    supervisor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='supervised_theses')
    year = models.IntegerField()
    department = models.CharField(max_length=100, default='CSE')
    research_area = models.CharField(max_length=200)
    document = models.FileField(upload_to='uploads/thesis/', blank=True, null=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='thesis_uploads')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-year']

    def __str__(self):
        return f"{self.title} ({self.year})"

class MentorshipRequest(models.Model):
    STATUS_CHOICES = [('pending', 'Pending'), ('accepted', 'Accepted'), ('declined', 'Declined')]
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mentorship_requests')
    mentor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mentorship_received')
    topic = models.CharField(max_length=300)
    message = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} -> {self.mentor} ({self.status})"

class ResearchGroup(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    research_area = models.CharField(max_length=200)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_groups')
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='research_groups', blank=True)
    mentor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='mentored_groups')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
