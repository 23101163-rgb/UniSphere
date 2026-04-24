
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import (
    ResearchGroup, ResearchJoinRequest, ResearchGroupInvitation,
    SupervisorRequest, KnowledgeAssessment, AssessmentQuestion,
    AssessmentSubmission, ResearchPaper, PaperReview
)
from notifications.models import Notification

User = get_user_model()


class ResearchGroupTests(TestCase):
    def setUp(self):
        self.student1 = User.objects.create_user(
            username='rstudent1', email='rstudent1@uap-bd.edu',
            password='testpass123', university_id='830001', role='student',
            first_name='Student', last_name='One'
        )
        self.student2 = User.objects.create_user(
            username='rstudent2', email='rstudent2@uap-bd.edu',
            password='testpass123', university_id='830002', role='student',
            first_name='Student', last_name='Two'
        )
        self.student3 = User.objects.create_user(
            username='rstudent3', email='rstudent3@uap-bd.edu',
            password='testpass123', university_id='830003', role='student',
            first_name='Student', last_name='Three'
        )
        self.student4 = User.objects.create_user(
            username='rstudent4', email='rstudent4@uap-bd.edu',
            password='testpass123', university_id='830004', role='student',
            first_name='Student', last_name='Four'
        )
        self.teacher1 = User.objects.create_user(
            username='rteacher1', email='rteacher1@uap-bd.edu',
            password='testpass123', university_id='830005', role='teacher',
            first_name='Teacher', last_name='One'
        )
        self.teacher2 = User.objects.create_user(
            username='rteacher2', email='rteacher2@uap-bd.edu',
            password='testpass123', university_id='830006', role='teacher',
            first_name='Teacher', last_name='Two'
        )

    def _create_open_group(self):
        group = ResearchGroup.objects.create(
            name='AI Research', description='AI group', research_area='AI',
            group_type='open', created_by=self.student1, status='forming'
        )
        group.members.add(self.student1)
        return group

    def _create_full_group(self):
        group = self._create_open_group()
        group.members.add(self.student2, self.student3, self.student4)
        return group

    # UT-043
    def test_group_create(self):
        self.client.login(username='rstudent1', password='testpass123')
        response = self.client.post(reverse('research:group_create'), {
            'name': 'NLP Group',
            'description': 'Natural Language Processing research',
            'research_area': 'NLP',
            'group_type': 'open',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        group = ResearchGroup.objects.get(name='NLP Group')
        self.assertEqual(group.created_by, self.student1)
        self.assertIn(self.student1, group.members.all())
        self.assertEqual(group.status, 'forming')

    # UT-044
    def test_join_open_group(self):
        group = self._create_open_group()
        self.client.login(username='rstudent2', password='testpass123')
        response = self.client.get(
            reverse('research:group_join', args=[group.pk]), follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            ResearchJoinRequest.objects.filter(
                group=group, requester=self.student2, status='pending'
            ).exists()
        )
        # Notification to creator
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.student1,
                title='New Research Group Join Request'
            ).exists()
        )

    # UT-045
    def test_invitation_closed_group(self):
        group = ResearchGroup.objects.create(
            name='Closed Group', description='Closed', research_area='Security',
            group_type='closed', created_by=self.student1, status='forming'
        )
        group.members.add(self.student1)

        # Creator invites student2
        self.client.login(username='rstudent1', password='testpass123')
        self.client.post(reverse('research:send_group_invitation', args=[group.pk]), {
            'invited_user': self.student2.pk,
        })
        invitation = ResearchGroupInvitation.objects.get(
            group=group, invited_user=self.student2
        )
        self.assertEqual(invitation.status, 'pending')

        # Student2 accepts
        self.client.login(username='rstudent2', password='testpass123')
        self.client.get(
            reverse('research:accept_group_invitation', args=[invitation.pk]),
            follow=True
        )
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, 'accepted')
        self.assertIn(self.student2, group.members.all())

    # UT-046
    def test_supervisor_request(self):
        group = self._create_full_group()

        self.client.login(username='rstudent1', password='testpass123')
        self.client.post(reverse('research:request_supervisor', args=[group.pk]), {
            'faculty': self.teacher1.pk,
            'message': 'Please supervise our AI research.',
        })

        sr = SupervisorRequest.objects.get(group=group, faculty=self.teacher1)
        self.assertEqual(sr.status, 'pending')
        group.refresh_from_db()
        self.assertEqual(group.status, 'pending_supervisor')

        # Teacher accepts
        self.client.login(username='rteacher1', password='testpass123')
        self.client.get(
            reverse('research:handle_supervisor_request', args=[sr.pk, 'accepted']),
            follow=True
        )
        sr.refresh_from_db()
        group.refresh_from_db()
        self.assertEqual(sr.status, 'accepted')
        self.assertEqual(group.supervisor, self.teacher1)
        self.assertEqual(group.status, 'active')


class ResearchAssessmentTests(TestCase):
    def setUp(self):
        self.student1 = User.objects.create_user(
            username='asstudent1', email='asstudent1@uap-bd.edu',
            password='testpass123', university_id='840001', role='student',
            first_name='AS', last_name='One'
        )
        self.teacher = User.objects.create_user(
            username='asteacher', email='asteacher@uap-bd.edu',
            password='testpass123', university_id='840002', role='teacher',
            first_name='AS', last_name='Teacher'
        )
        self.group = ResearchGroup.objects.create(
            name='Assessment Group', description='Test', research_area='ML',
            group_type='open', created_by=self.student1,
            supervisor=self.teacher, status='assessment'
        )
        self.group.members.add(self.student1)

        # Create assessment with 2 questions
        self.assessment = KnowledgeAssessment.objects.create(
            group=self.group, title='ML Quiz', created_by=self.teacher, passing_score=50
        )
        self.q1 = AssessmentQuestion.objects.create(
            assessment=self.assessment,
            question_text='What is supervised learning?',
            option_a='Learning with labels', option_b='Learning without labels',
            option_c='Reinforcement', option_d='None',
            correct_option='a'
        )
        self.q2 = AssessmentQuestion.objects.create(
            assessment=self.assessment,
            question_text='What is overfitting?',
            option_a='Too little data', option_b='Model too complex',
            option_c='Model too simple', option_d='None',
            correct_option='b'
        )

    # UT-047
    def test_assessment_pass(self):
        self.client.login(username='asstudent1', password='testpass123')
        response = self.client.post(
            reverse('research:take_assessment', args=[self.assessment.pk]), {
                f'question_{self.q1.pk}': 'a',  # correct
                f'question_{self.q2.pk}': 'b',  # correct
            }, follow=True
        )
        self.assertEqual(response.status_code, 200)
        submission = AssessmentSubmission.objects.get(
            assessment=self.assessment, student=self.student1
        )
        self.assertTrue(submission.passed)
        self.assertEqual(submission.score, 2)
        self.assertEqual(submission.total, 2)

    # UT-048
    def test_assessment_fail(self):
        # Change passing score to 100 so student fails
        self.assessment.passing_score = 100
        self.assessment.save()

        self.client.login(username='asstudent1', password='testpass123')
        self.client.post(
            reverse('research:take_assessment', args=[self.assessment.pk]), {
                f'question_{self.q1.pk}': 'a',  # correct
                f'question_{self.q2.pk}': 'c',  # wrong
            }
        )
        submission = AssessmentSubmission.objects.get(
            assessment=self.assessment, student=self.student1
        )
        self.assertFalse(submission.passed)
        self.assertEqual(submission.score, 1)


class ResearchPaperTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username='paperstudent', email='paperstudent@uap-bd.edu',
            password='testpass123', university_id='850001', role='student',
            first_name='Paper', last_name='Student'
        )
        self.supervisor = User.objects.create_user(
            username='papersup', email='papersup@uap-bd.edu',
            password='testpass123', university_id='850002', role='teacher',
            first_name='Paper', last_name='Supervisor'
        )
        self.cosupervisor = User.objects.create_user(
            username='papercosup', email='papercosup@uap-bd.edu',
            password='testpass123', university_id='850003', role='teacher',
            first_name='Paper', last_name='CoSupervisor'
        )
        self.group = ResearchGroup.objects.create(
            name='Paper Group', description='Test', research_area='CV',
            group_type='open', created_by=self.student,
            supervisor=self.supervisor, co_supervisor=self.cosupervisor,
            status='paper_writing'
        )
        self.group.members.add(self.student)
        self.test_pdf = SimpleUploadedFile(
            'paper.pdf', b'%PDF-1.4 paper content', content_type='application/pdf'
        )

    # UT-049
    def test_paper_submit_and_review(self):
        self.client.login(username='paperstudent', password='testpass123')
        response = self.client.post(
            reverse('research:submit_paper', args=[self.group.pk]), {
                'title': 'CV in Agriculture',
                'abstract': 'Using CV for crop detection',
                'document': self.test_pdf,
            }, follow=True
        )
        self.assertEqual(response.status_code, 200)
        paper = ResearchPaper.objects.get(title='CV in Agriculture')
        self.assertEqual(paper.status, 'submitted')

        # Supervisor reviews — approve
        self.client.login(username='papersup', password='testpass123')
        self.client.post(reverse('research:review_paper', args=[paper.pk]), {
            'feedback': 'Good work, approved.',
            'is_approved': True,
        })
        review = PaperReview.objects.get(paper=paper, reviewer=self.supervisor)
        self.assertTrue(review.is_approved)

    # UT-050
    def test_publish_paper(self):
        paper = ResearchPaper.objects.create(
            group=self.group, title='Published Paper', abstract='Test',
            document=self.test_pdf, submitted_by=self.student, status='submitted'
        )
        # Both reviewers approve
        PaperReview.objects.create(
            paper=paper, reviewer=self.supervisor,
            feedback='Approved', is_approved=True
        )
        PaperReview.objects.create(
            paper=paper, reviewer=self.cosupervisor,
            feedback='Approved', is_approved=True
        )
        paper.status = 'approved'
        paper.save()

        # Supervisor publishes
        self.client.login(username='papersup', password='testpass123')
        self.client.get(
            reverse('research:publish_paper', args=[paper.pk]), follow=True
        )
        paper.refresh_from_db()
        self.group.refresh_from_db()
        self.assertEqual(paper.status, 'published')
        self.assertEqual(self.group.status, 'published')

    # Extra: revision flow
    def test_paper_revision_flow(self):
        paper = ResearchPaper.objects.create(
            group=self.group, title='Revision Paper', abstract='Test',
            document=self.test_pdf, submitted_by=self.student, status='submitted'
        )
        self.group.status = 'evaluation'
        self.group.save()

        # Supervisor rejects
        self.client.login(username='papersup', password='testpass123')
        self.client.post(reverse('research:review_paper', args=[paper.pk]), {
            'feedback': 'Needs more data.',
            'is_approved': False,
        })
        paper.refresh_from_db()
        self.group.refresh_from_db()
        self.assertEqual(paper.status, 'revision')
        self.assertEqual(self.group.status, 'paper_writing')