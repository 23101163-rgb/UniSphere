from django.db import models
from django.conf import settings


class StudyMaterial(models.Model):
    SEMESTER_CHOICES = [
        (f'{i}.{j}', f'Year {i} Semester {j}')
        for i in range(1, 5)
        for j in range(1, 3)
    ]

    title = models.CharField(max_length=300)
    description = models.TextField()
    course_name = models.CharField(max_length=200, db_index=True)
    semester = models.CharField(max_length=10, choices=SEMESTER_CHOICES, db_index=True)
    topic = models.CharField(max_length=200)
    tags = models.CharField(max_length=500, blank=True, help_text='Comma-separated tags')
    file = models.FileField(upload_to='uploads/materials/')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='materials'
    )
    is_approved = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    download_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def average_rating(self):
        avg = self.ratings.aggregate(models.Avg('score'))['score__avg']
        return round(avg, 1) if avg is not None else 0

    def tag_list(self):
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]

    def total_ratings(self):
        return self.ratings.count()


class MaterialRating(models.Model):
    material = models.ForeignKey(
        StudyMaterial,
        on_delete=models.CASCADE,
        related_name='ratings'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    score = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('material', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} rated {self.material.title} ({self.score})'


class Bookmark(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookmarks'
    )
    material = models.ForeignKey(
        StudyMaterial,
        on_delete=models.CASCADE,
        related_name='bookmarks'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'material')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} bookmarked {self.material.title}'