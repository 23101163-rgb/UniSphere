from django.db import models
from django.conf import settings

class ResearchGroup(models.Model):
    STATUS_CHOICES = [
        ('forming', 'Forming - Collecting Members'),
        ('pending_supervisor', 'Pending Supervisor Approval'),
        ('active', 'Active - Supervisor Confirmed'),
        ('pending_cosupervisor', 'Pending Co-Supervisor Approval'),
        ('topic_selection', 'Topic Selection Phase'),
        ('assessment', 'Knowledge Assessment Phase'),
        ('paper_study', 'Research Paper Study Phase'),
        ('paper_writing', 'Paper Writing Phase'),
        ('evaluation', 'Evaluation Phase'),
        ('published', 'Published'),
    ]

    GROUP_TYPE_CHOICES = [
        ('open', 'Open Group'),
        ('closed', 'Closed Group'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()
    research_area = models.CharField(max_length=200)
    research_topic = models.CharField(max_length=300, blank=True)
    group_type = models.CharField(max_length=10, choices=GROUP_TYPE_CHOICES, default='open')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='rg_created_groups'
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='rg_research_groups', blank=True
    )
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='rg_supervised_groups'
    )
    co_supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='rg_co_supervised_groups'
    )
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='forming')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def member_count(self):
        return self.members.count()

    def is_full(self):
        return self.members.count() >= 4

    def all_assessments_passed(self):
        """Check if all members have passed in any assessment of this group"""
        if not self.members.exists():
            return False

        for member in self.members.all():
            has_passed = AssessmentSubmission.objects.filter(
                assessment__group=self,
                student=member,
                passed=True
            ).exists()
            if not has_passed:
                return False

        return True



class ResearchJoinRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ]

    group = models.ForeignKey(
        ResearchGroup, on_delete=models.CASCADE,
        related_name='join_requests'
    )
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='research_join_requests'
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.requester.get_full_name()} -> {self.group.name} ({self.status})"


# ===================== CLOSED GROUP INVITATION =====================
class ResearchGroupInvitation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ]

    group = models.ForeignKey(
        ResearchGroup, on_delete=models.CASCADE,
        related_name='invitations'
    )
    invited_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='research_group_invitations'
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='research_group_invitations_sent'
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.group.name} -> {self.invited_user.get_full_name()} ({self.status})"


# ===================== SUPERVISOR REQUEST =====================
class SupervisorRequest(models.Model):
    REQUEST_TYPE_CHOICES = [
        ('supervisor', 'Supervisor'),
        ('co_supervisor', 'Co-Supervisor'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ]

    group = models.ForeignKey(
        ResearchGroup, on_delete=models.CASCADE,
        related_name='supervisor_requests'
    )
    faculty = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='supervisor_requests_received'
    )
    request_type = models.CharField(max_length=15, choices=REQUEST_TYPE_CHOICES)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='supervisor_requests_sent'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.group.name} -> {self.faculty.get_full_name()} ({self.request_type})"


# ===================== KNOWLEDGE ASSESSMENT =====================
class KnowledgeAssessment(models.Model):
    group = models.ForeignKey(
        ResearchGroup, on_delete=models.CASCADE,
        related_name='assessments'
    )
    title = models.CharField(max_length=300)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    passing_score = models.IntegerField(default=60, help_text='Passing percentage')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.group.name}"


class AssessmentQuestion(models.Model):
    assessment = models.ForeignKey(
        KnowledgeAssessment, on_delete=models.CASCADE,
        related_name='questions'
    )
    question_text = models.TextField()
    option_a = models.CharField(max_length=500)
    option_b = models.CharField(max_length=500)
    option_c = models.CharField(max_length=500)
    option_d = models.CharField(max_length=500)
    correct_option = models.CharField(
        max_length=1,
        choices=[('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D')]
    )

    def __str__(self):
        return self.question_text[:50]


class AssessmentSubmission(models.Model):
    assessment = models.ForeignKey(
        KnowledgeAssessment, on_delete=models.CASCADE,
        related_name='submissions'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    score = models.IntegerField(default=0)
    total = models.IntegerField(default=0)
    passed = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('assessment', 'student')

    def percentage(self):
        if self.total == 0:
            return 0
        return round((self.score / self.total) * 100)


# ===================== REFERENCE PAPERS =====================
class ReferencePaper(models.Model):
    group = models.ForeignKey(
        ResearchGroup, on_delete=models.CASCADE,
        related_name='reference_papers'
    )
    title = models.CharField(max_length=500)
    url = models.URLField()
    description = models.TextField(blank=True)
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# ===================== RESEARCH PAPER (Student's own) =====================
class ResearchPaper(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted for Review'),
        ('revision', 'Needs Revision'),
        ('approved', 'Approved'),
        ('published', 'Published'),
    ]

    group = models.ForeignKey(
        ResearchGroup, on_delete=models.CASCADE,
        related_name='papers'
    )
    title = models.CharField(max_length=500)
    abstract = models.TextField()
    document = models.FileField(upload_to='uploads/research_papers/')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def is_fully_reviewed(self):
        """Both supervisor and co-supervisor reviewed"""
        return self.reviews.count() >= 2

    def is_approved_by_both(self):
        """Both reviewers approved"""
        return (
            self.reviews.filter(is_approved=True).count() >= 2
        )


class PaperReview(models.Model):
    paper = models.ForeignKey(
        ResearchPaper, on_delete=models.CASCADE,
        related_name='reviews'
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    feedback = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('paper', 'reviewer')

    def __str__(self):
        status = "Approved" if self.is_approved else "Needs Revision"
        return f"{self.reviewer.get_full_name()} - {status}"