from django.db import models
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

class Thread(models.Model):
    title = models.CharField(max_length=300)
    content = models.TextField()
    image = models.ImageField(upload_to='uploads/forum/', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='threads')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='threads')
    is_pinned = models.BooleanField(default=False)
    is_flagged = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return self.title

    def reply_count(self):
        return self.replies.count()

    def upvote_count(self):
        return self.votes.filter(vote_type='up').count()

class Reply(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='replies')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    is_flagged = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def upvote_count(self):
        return self.votes.filter(vote_type='up').count()

class Vote(models.Model):
    VOTE_CHOICES = [('up', 'Upvote'), ('down', 'Downvote')]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, null=True, blank=True, related_name='votes')
    reply = models.ForeignKey(Reply, on_delete=models.CASCADE, null=True, blank=True, related_name='votes')
    vote_type = models.CharField(max_length=4, choices=VOTE_CHOICES)

    class Meta:
        unique_together = [('user', 'thread'), ('user', 'reply')]
