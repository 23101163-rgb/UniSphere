from django.db import models
from django.conf import settings

class Complaint(models.Model):
    CATEGORY_CHOICES = [
        ('academic', 'Academic'),
        ('infrastructure', 'Infrastructure'),
        ('harassment', 'Harassment'),
        ('administration', 'Administration'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('in_review', 'In Review'),
        ('under_investigation', 'Under Investigation'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    TARGET_CHOICES = [
        ('admin', 'Admin / University'),
        ('teacher', 'Specific Teacher'),
    ]

    subject = models.CharField(max_length=300)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='complaints')
    is_anonymous = models.BooleanField(default=False)
    admin_response = models.TextField(blank=True)

    # ✅ NEW: Complaint target
    target_type = models.CharField(max_length=10, choices=TARGET_CHOICES, default='admin')
    target_teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='received_complaints'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject} ({self.status})"