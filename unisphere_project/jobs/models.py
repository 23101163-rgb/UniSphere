from django.db import models
from django.conf import settings

class JobListing(models.Model):
    TYPE_CHOICES = [('job', 'Job'), ('internship', 'Internship')]
    title = models.CharField(max_length=300)
    company_name = models.CharField(max_length=200)
    job_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    description = models.TextField()
    required_skills = models.TextField()
    eligibility = models.TextField(blank=True)
    salary_range = models.CharField(max_length=100, blank=True)
    application_deadline = models.DateField()
    application_link = models.URLField()
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='job_posts')
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} at {self.company_name}"

class JobBookmark(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='job_bookmarks')
    job = models.ForeignKey(JobListing, on_delete=models.CASCADE, related_name='bookmarks')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'job')
class JobApplication(models.Model):
    job = models.ForeignKey(JobListing, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='job_applications')
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    cover_letter = models.TextField(blank=True)
    cv_link = models.URLField(blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('job', 'applicant')
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.applicant.username} -> {self.job.title}"

