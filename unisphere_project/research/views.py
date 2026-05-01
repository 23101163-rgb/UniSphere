from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from notifications.utils import create_notification

from .models import (
    ResearchGroup, ResearchJoinRequest, ResearchGroupInvitation,
    SupervisorRequest, KnowledgeAssessment, AssessmentQuestion,
    AssessmentSubmission, ReferencePaper, ResearchPaper, PaperReview
)
from .forms import (
    ResearchGroupForm, ResearchGroupInvitationForm,
    SupervisorRequestForm, TopicSelectionForm, AssessmentForm,
    AssessmentQuestionForm, ReferencePaperForm, ResearchPaperForm,
    PaperReviewForm
)
from accounts.models import User


# ==================== RESEARCH GROUP ====================
@login_required
def research_group_list(request):
    if request.user.role == 'teacher':
        groups = ResearchGroup.objects.filter(
            Q(supervisor=request.user) | Q(co_supervisor=request.user)
        ).distinct().order_by('-created_at')
    else:
        groups = ResearchGroup.objects.all().order_by('-created_at')

    pending_join_request_group_ids = []
    pending_invitation_group_ids = []

    if request.user.role in ['student', 'alumni']:
        pending_join_request_group_ids = list(
            ResearchJoinRequest.objects.filter(
                requester=request.user,
                status='pending'
            ).values_list('group_id', flat=True)
        )

        pending_invitation_group_ids = list(
            ResearchGroupInvitation.objects.filter(
                invited_user=request.user,
                status='pending'
            ).values_list('group_id', flat=True)
        )

    return render(request, 'research/group_list.html', {
        'groups': groups,
        'pending_join_request_group_ids': pending_join_request_group_ids,
        'pending_invitation_group_ids': pending_invitation_group_ids,
    })


@login_required
def research_group_create(request):
    if request.user.role not in ['student', 'alumni']:
        messages.error(request, 'Only students and alumni can create research groups.')
        return redirect('research:groups')

    if request.method == 'POST':
        form = ResearchGroupForm(request.POST)
        if form.is_valid():
            g = form.save(commit=False)
            g.created_by = request.user
            g.status = 'forming'
            g.save()
            g.members.add(request.user)

            if g.group_type == 'open':
                messages.success(request, 'Open research group created! Others can request to join, and you can approve them.')
            else:
                messages.success(request, 'Closed research group created! You can now invite students/alumni to join.')

            return redirect('research:group_detail', pk=g.pk)
    else:
        form = ResearchGroupForm()

    return render(request, 'research/group_form.html', {'form': form})


@login_required
def group_detail(request, pk):
    group = get_object_or_404(ResearchGroup, pk=pk)
    if request.user.role == 'teacher' and request.user not in [group.supervisor, group.co_supervisor]:
        messages.error(request, 'You can only view groups you supervise or co-supervise.')
        return redirect('research:groups')
    is_member = request.user in group.members.all()
    is_supervisor = request.user == group.supervisor
    is_cosupervisor = request.user == group.co_supervisor
    is_creator = request.user == group.created_by

    latest_assessment = group.assessments.order_by('-created_at').first()
    user_submission = None
    user_passed_any_assessment = False

    if is_member:
        user_passed_any_assessment = AssessmentSubmission.objects.filter(
            assessment__group=group,
            student=request.user,
            passed=True
        ).exists()

        if latest_assessment:
            user_submission = latest_assessment.submissions.filter(student=request.user).first()

    papers = group.papers.all()
    reference_papers = group.reference_papers.all()

    my_join_request = None
    my_invitation = None
    pending_join_requests = []
    pending_invitations = []
    invitation_form = None

    if request.user.role in ['student', 'alumni']:
        my_join_request = ResearchJoinRequest.objects.filter(
            group=group,
            requester=request.user,
            status='pending'
        ).first()

        my_invitation = ResearchGroupInvitation.objects.filter(
            group=group,
            invited_user=request.user,
            status='pending'
        ).first()

    if is_creator and group.status == 'forming':
        if group.group_type == 'open':
            pending_join_requests = group.join_requests.filter(status='pending').order_by('-requested_at')

        elif group.group_type == 'closed':
            pending_invitations = group.invitations.filter(status='pending').order_by('-created_at')

            invitation_form = ResearchGroupInvitationForm()
            existing_member_ids = group.members.values_list('id', flat=True)
            pending_invited_ids = group.invitations.filter(status='pending').values_list('invited_user_id', flat=True)

            invitation_form.fields['invited_user'].queryset = User.objects.filter(
                role__in=['student', 'alumni']
            ).exclude(
                id__in=existing_member_ids
            ).exclude(
                id__in=pending_invited_ids
            ).exclude(
                id=group.created_by_id
            )

    context = {
        'group': group,
        'is_member': is_member,
        'is_supervisor': is_supervisor,
        'is_cosupervisor': is_cosupervisor,
        'is_creator': is_creator,
        'latest_assessment': latest_assessment,
        'user_submission': user_submission,
        'user_passed_any_assessment': user_passed_any_assessment,
        'papers': papers,
        'reference_papers': reference_papers,

        'my_join_request': my_join_request,
        'my_invitation': my_invitation,
        'pending_join_requests': pending_join_requests,
        'pending_invitations': pending_invitations,
        'invitation_form': invitation_form,
    }
    return render(request, 'research/group_detail.html', context)


@login_required
def research_group_join(request, pk):
    group = get_object_or_404(ResearchGroup, pk=pk)

    if group.group_type != 'open':
        messages.error(request, 'This is a closed group. Only invited users can join.')
        return redirect('research:group_detail', pk=pk)

    if group.status != 'forming':
        messages.error(request, 'This group is no longer accepting members.')
        return redirect('research:group_detail', pk=pk)

    if group.is_full():
        messages.error(request, 'This group is already full (4 members).')
        return redirect('research:group_detail', pk=pk)

    if request.user.role not in ['student', 'alumni']:
        messages.error(request, 'Only students and alumni can request to join groups.')
        return redirect('research:group_detail', pk=pk)

    if request.user == group.created_by:
        messages.info(request, 'You are the creator of this group.')
        return redirect('research:group_detail', pk=pk)

    if request.user in group.members.all():
        messages.info(request, 'You are already a member of this group.')
        return redirect('research:group_detail', pk=pk)

    existing = ResearchJoinRequest.objects.filter(
        group=group,
        requester=request.user,
        status='pending'
    ).first()
    if existing:
        messages.info(request, 'You already sent a join request to this group.')
        return redirect('research:group_detail', pk=pk)

    ResearchJoinRequest.objects.create(
        group=group,
        requester=request.user
    )

    create_notification(
        recipient=group.created_by,
        title='New Research Group Join Request',
        message=f'{request.user.get_full_name()} requested to join your research group "{group.name}".',
        link=f'/research/groups/{group.pk}/'
    )

    messages.success(request, f'Join request sent to "{group.name}". Wait for creator approval.')
    return redirect('research:group_detail', pk=pk)

@login_required
def approve_join_request(request, request_pk):
    join_request = get_object_or_404(
        ResearchJoinRequest,
        pk=request_pk,
        group__created_by=request.user,
        status='pending'
    )
    group = join_request.group

    if group.group_type != 'open':
        messages.error(request, 'This action is only for open groups.')
        return redirect('research:group_detail', pk=group.pk)

    if group.status != 'forming':
        messages.error(request, 'This group is no longer accepting members.')
        return redirect('research:group_detail', pk=group.pk)

    if group.is_full():
        messages.error(request, 'Group is already full.')
        return redirect('research:group_detail', pk=group.pk)

    if join_request.requester in group.members.all():
        join_request.status = 'accepted'
        join_request.responded_at = timezone.now()
        join_request.save()
        messages.info(request, 'This user is already a member.')
        return redirect('research:group_detail', pk=group.pk)

    group.members.add(join_request.requester)
    join_request.status = 'accepted'
    join_request.responded_at = timezone.now()
    join_request.save()

    create_notification(
        recipient=join_request.requester,
        title='Research Group Join Request Approved',
        message=f'Your join request for "{group.name}" has been approved.',
        link=f'/research/groups/{group.pk}/'
    )

    messages.success(request, f'{join_request.requester.get_full_name()} joined the group.')
    return redirect('research:group_detail', pk=group.pk)
@login_required
def decline_join_request(request, request_pk):
    join_request = get_object_or_404(
        ResearchJoinRequest,
        pk=request_pk,
        group__created_by=request.user,
        status='pending'
    )
    group = join_request.group

    join_request.status = 'declined'
    join_request.responded_at = timezone.now()
    join_request.save()

    create_notification(
        recipient=join_request.requester,
        title='Research Group Join Request Declined',
        message=f'Your join request for "{group.name}" has been declined.',
        link=f'/research/groups/{group.pk}/'
    )

    messages.info(request, 'Join request declined.')
    return redirect('research:group_detail', pk=group.pk)


@login_required
def send_group_invitation(request, pk):
    group = get_object_or_404(ResearchGroup, pk=pk)

    if request.user != group.created_by:
        messages.error(request, 'Only group creator can send invitations.')
        return redirect('research:group_detail', pk=pk)

    if group.group_type != 'closed':
        messages.error(request, 'Invitations are only for closed groups.')
        return redirect('research:group_detail', pk=pk)

    if group.status != 'forming':
        messages.error(request, 'Cannot invite members after group is confirmed.')
        return redirect('research:group_detail', pk=pk)

    if group.is_full():
        messages.error(request, 'This group is already full (4 members).')
        return redirect('research:group_detail', pk=pk)

    if request.method == 'POST':
        form = ResearchGroupInvitationForm(request.POST)

        existing_member_ids = group.members.values_list('id', flat=True)
        pending_invited_ids = group.invitations.filter(status='pending').values_list('invited_user_id', flat=True)

        form.fields['invited_user'].queryset = User.objects.filter(
            role__in=['student', 'alumni']
        ).exclude(
            id__in=existing_member_ids
        ).exclude(
            id__in=pending_invited_ids
        ).exclude(
            id=group.created_by_id
        )

        if form.is_valid():
            invited_user = form.cleaned_data['invited_user']

            if invited_user in group.members.all():
                messages.info(request, 'This user is already a member.')
                return redirect('research:group_detail', pk=pk)

            existing = ResearchGroupInvitation.objects.filter(
                group=group,
                invited_user=invited_user,
                status='pending'
            ).first()
            if existing:
                messages.info(request, 'A pending invitation already exists for this user.')
                return redirect('research:group_detail', pk=pk)

            invitation = ResearchGroupInvitation.objects.create(
                group=group,
                invited_user=invited_user,
                invited_by=request.user
            )

            accept_url = request.build_absolute_uri(
                reverse('research:accept_group_invitation', args=[invitation.pk])
            )

            email_sent = False
            try:
                send_mail(
                    subject=f'Research Group Invitation: {group.name}',
                    message=(
                        f'Hello {invited_user.get_full_name() or invited_user.username},\n\n'
                        f'{request.user.get_full_name() or request.user.username} invited you to join the closed research group "{group.name}".\n\n'
                        f'Accept invitation: {accept_url}\n\n'
                        'This is an invitation-only closed group.'
                    ),
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                    recipient_list=[invited_user.email],
                    fail_silently=False,
                )
                email_sent = True
            except Exception as exc:
                messages.warning(
                    request,
                    f'Invitation notification was created, but email could not be sent: {exc}'
                )

            create_notification(
                recipient=invited_user,
                title='Research Group Invitation',
                message=f'You have been invited to join the research group "{group.name}".',
                link=f'/research/groups/{group.pk}/'
            )

            if email_sent:
                messages.success(request, f'Invitation sent to {invited_user.get_full_name()} by real email and notification.')
            else:
                messages.success(request, f'Invitation notification sent to {invited_user.get_full_name()}. Email failed; check SMTP settings.')
            return redirect('research:group_detail', pk=pk)

    messages.error(request, 'Invalid invitation request.')
    return redirect('research:group_detail', pk=pk)


@login_required
def accept_group_invitation(request, invitation_pk):
    invitation = get_object_or_404(
        ResearchGroupInvitation,
        pk=invitation_pk,
        invited_user=request.user,
        status='pending'
    )
    group = invitation.group

    if group.group_type != 'closed':
        messages.error(request, 'This invitation is not valid.')
        return redirect('research:group_detail', pk=group.pk)

    if group.status != 'forming':
        messages.error(request, 'This group is no longer accepting members.')
        return redirect('research:group_detail', pk=group.pk)

    if group.is_full():
        messages.error(request, 'This group is already full.')
        return redirect('research:group_detail', pk=group.pk)

    if request.user in group.members.all():
        invitation.status = 'accepted'
        invitation.responded_at = timezone.now()
        invitation.save()
        messages.info(request, 'You are already a member of this group.')
        return redirect('research:group_detail', pk=group.pk)

    group.members.add(request.user)
    invitation.status = 'accepted'
    invitation.responded_at = timezone.now()
    invitation.save()

    create_notification(
        recipient=group.created_by,
        title='Research Group Invitation Accepted',
        message=f'{request.user.get_full_name()} accepted your invitation to join "{group.name}".',
        link=f'/research/groups/{group.pk}/'
    )

    messages.success(request, f'You joined "{group.name}".')
    return redirect('research:group_detail', pk=group.pk)

@login_required
def decline_group_invitation(request, invitation_pk):
    invitation = get_object_or_404(
        ResearchGroupInvitation,
        pk=invitation_pk,
        invited_user=request.user,
        status='pending'
    )
    group = invitation.group

    invitation.status = 'declined'
    invitation.responded_at = timezone.now()
    invitation.save()

    create_notification(
        recipient=group.created_by,
        title='Research Group Invitation Declined',
        message=f'{request.user.get_full_name()} declined your invitation to join "{group.name}".',
        link=f'/research/groups/{group.pk}/'
    )

    messages.info(request, 'Invitation declined.')
    return redirect('research:group_detail', pk=group.pk)


@login_required
def research_group_leave(request, pk):
    group = get_object_or_404(ResearchGroup, pk=pk)
    if group.status != 'forming':
        messages.error(request, 'Cannot leave after group is confirmed.')
        return redirect('research:group_detail', pk=pk)

    if request.user == group.created_by:
        messages.error(request, 'Group creator cannot leave the group.')
        return redirect('research:group_detail', pk=pk)

    group.members.remove(request.user)
    messages.success(request, 'You left the group.')
    return redirect('research:groups')


# ==================== SUPERVISOR REQUEST ====================
@login_required
def request_supervisor(request, pk):
    group = get_object_or_404(ResearchGroup, pk=pk)
    if request.user != group.created_by:
        messages.error(request, 'Only group creator can request a supervisor.')
        return redirect('research:group_detail', pk=pk)
    if not group.is_full():
        messages.error(request, 'Group must have 4 members before requesting a supervisor.')
        return redirect('research:group_detail', pk=pk)

    if request.method == 'POST':
        form = SupervisorRequestForm(request.POST)
        if form.is_valid():
            faculty = form.cleaned_data['faculty']
            msg = form.cleaned_data['message']
            existing = SupervisorRequest.objects.filter(
                group=group, faculty=faculty,
                request_type='supervisor', status='pending'
            ).exists()
            if existing:
                messages.warning(request, 'A pending request already exists for this faculty.')
            else:
                SupervisorRequest.objects.create(
                    group=group, faculty=faculty,
                    request_type='supervisor', message=msg,
                    requested_by=request.user
                )
                group.status = 'pending_supervisor'
                group.save()

                create_notification(
                    recipient=faculty,
                    title='New Supervisor Request',
                    message=f'{request.user.get_full_name()} requested you to supervise the research group "{group.name}".',
                    link=f'/research/supervisor-requests/'
                )

                messages.success(request, f'Supervisor request sent to {faculty.get_full_name()}!')
            return redirect('research:group_detail', pk=pk)
    else:
        form = SupervisorRequestForm()
    return render(request, 'research/request_supervisor.html', {'form': form, 'group': group})

@login_required
def my_supervisor_requests(request):
    requests_list = SupervisorRequest.objects.filter(
        faculty=request.user
    ).order_by('-created_at')
    return render(request, 'research/supervisor_requests.html', {'requests_list': requests_list})


@login_required
def handle_supervisor_request(request, pk, action):
    sr = get_object_or_404(SupervisorRequest, pk=pk, faculty=request.user)
    group = sr.group

    if action == 'accepted':
        sr.status = 'accepted'
        sr.save()

        if sr.request_type == 'supervisor':
            group.supervisor = request.user
            group.status = 'active'
            group.save()

            create_notification(
                recipient=sr.requested_by,
                title='Supervisor Request Accepted',
                message=f'{request.user.get_full_name()} accepted your supervisor request for the group "{group.name}".',
                link=f'/research/groups/{group.pk}/'
            )

            messages.success(request, f'You are now supervisor of "{group.name}"!')

        elif sr.request_type == 'co_supervisor':
            group.co_supervisor = request.user
            group.status = 'topic_selection'
            group.save()

            create_notification(
                recipient=sr.requested_by,
                title='Co-Supervisor Request Accepted',
                message=f'{request.user.get_full_name()} accepted your co-supervisor request for the group "{group.name}".',
                link=f'/research/groups/{group.pk}/'
            )

            messages.success(request, f'You are now co-supervisor of "{group.name}"!')

    elif action == 'declined':
        sr.status = 'declined'
        sr.save()

        if sr.request_type == 'supervisor':
            group.status = 'forming'
            group.save()

            create_notification(
                recipient=sr.requested_by,
                title='Supervisor Request Declined',
                message=f'{request.user.get_full_name()} declined your supervisor request for the group "{group.name}".',
                link=f'/research/groups/{group.pk}/'
            )

        elif sr.request_type == 'co_supervisor':
            group.status = 'active'
            group.save()

            create_notification(
                recipient=sr.requested_by,
                title='Co-Supervisor Request Declined',
                message=f'{request.user.get_full_name()} declined your co-supervisor request for the group "{group.name}".',
                link=f'/research/groups/{group.pk}/'
            )

        messages.info(request, 'Request declined.')

    return redirect('research:my_supervisor_requests')


# ==================== CO-SUPERVISOR REQUEST ====================
@login_required
def request_cosupervisor(request, pk):
    group = get_object_or_404(ResearchGroup, pk=pk)
    if request.user != group.supervisor:
        messages.error(request, 'Only the supervisor can request a co-supervisor.')
        return redirect('research:group_detail', pk=pk)

    if request.method == 'POST':
        form = SupervisorRequestForm(request.POST)
        if form.is_valid():
            faculty = form.cleaned_data['faculty']
            if faculty == group.supervisor:
                messages.error(request, 'Co-supervisor must be a different faculty member.')
                return redirect('research:request_cosupervisor', pk=pk)

            msg = form.cleaned_data['message']

            existing = SupervisorRequest.objects.filter(
                group=group,
                faculty=faculty,
                request_type='co_supervisor',
                status='pending'
            ).exists()

            if existing:
                messages.warning(request, 'A pending co-supervisor request already exists for this faculty.')
            else:
                SupervisorRequest.objects.create(
                    group=group,
                    faculty=faculty,
                    request_type='co_supervisor',
                    message=msg,
                    requested_by=request.user
                )
                group.status = 'pending_cosupervisor'
                group.save()

                create_notification(
                    recipient=faculty,
                    title='New Co-Supervisor Request',
                    message=f'{request.user.get_full_name()} requested you to co-supervise the research group "{group.name}".',
                    link='/research/supervisor-requests/'
                )

                messages.success(request, f'Co-supervisor request sent to {faculty.get_full_name()}!')

            return redirect('research:group_detail', pk=pk)
    else:
        form = SupervisorRequestForm()

    return render(request, 'research/request_cosupervisor.html', {'form': form, 'group': group})
# ==================== TOPIC SELECTION ====================
@login_required
def select_topic(request, pk):
    group = get_object_or_404(ResearchGroup, pk=pk)
    if request.user not in [group.supervisor, group.co_supervisor]:
        messages.error(request, 'Only supervisor or co-supervisor can select the topic.')
        return redirect('research:group_detail', pk=pk)

    if request.method == 'POST':
        form = TopicSelectionForm(request.POST)
        if form.is_valid():
            group.research_topic = form.cleaned_data['research_topic']
            group.status = 'assessment'
            group.save()
            messages.success(request, f'Topic "{group.research_topic}" selected!')
            return redirect('research:group_detail', pk=pk)
    else:
        form = TopicSelectionForm()
    return render(request, 'research/select_topic.html', {'form': form, 'group': group})


# ==================== KNOWLEDGE ASSESSMENT ====================
@login_required
def create_assessment(request, pk):
    group = get_object_or_404(ResearchGroup, pk=pk)
    if request.user not in [group.supervisor, group.co_supervisor]:
        messages.error(request, 'Only supervisor or co-supervisor can create assessments.')
        return redirect('research:group_detail', pk=pk)

    if request.method == 'POST':
        form = AssessmentForm(request.POST)
        if form.is_valid():
            a = form.save(commit=False)
            a.group = group
            a.created_by = request.user
            a.save()
            messages.success(request, 'Assessment created! Now add questions.')
            return redirect('research:add_question', assessment_pk=a.pk)
    else:
        form = AssessmentForm()
    return render(request, 'research/create_assessment.html', {'form': form, 'group': group})


@login_required
def add_question(request, assessment_pk):
    assessment = get_object_or_404(KnowledgeAssessment, pk=assessment_pk)
    group = assessment.group

    if request.user not in [group.supervisor, group.co_supervisor]:
        messages.error(request, 'Only supervisor or co-supervisor can add questions.')
        return redirect('research:group_detail', pk=group.pk)

    if request.method == 'POST':
        form = AssessmentQuestionForm(request.POST)
        if form.is_valid():
            q = form.save(commit=False)
            q.assessment = assessment
            q.save()
            messages.success(request, 'Question added!')
            if 'add_another' in request.POST:
                return redirect('research:add_question', assessment_pk=assessment.pk)
            return redirect('research:group_detail', pk=assessment.group.pk)
    else:
        form = AssessmentQuestionForm()

    questions = assessment.questions.all()
    return render(request, 'research/add_question.html', {
        'form': form, 'assessment': assessment, 'questions': questions
    })


@login_required
def take_assessment(request, assessment_pk):
    assessment = get_object_or_404(KnowledgeAssessment, pk=assessment_pk)
    group = assessment.group

    if request.user not in group.members.all():
        messages.error(request, 'Only group members can take assessments.')
        return redirect('research:group_detail', pk=group.pk)

    already_passed = AssessmentSubmission.objects.filter(
        assessment__group=group,
        student=request.user,
        passed=True
    ).exists()
    if already_passed:
        messages.info(request, 'You have already passed the assessment stage for this group.')
        return redirect('research:group_detail', pk=group.pk)

    existing = AssessmentSubmission.objects.filter(
        assessment=assessment, student=request.user
    ).first()
    if existing:
        messages.info(request, f'You already took this assessment. Score: {existing.percentage()}%')
        return redirect('research:group_detail', pk=group.pk)

    questions = assessment.questions.all()

    if request.method == 'POST':
        score = 0
        total = questions.count()
        for q in questions:
            answer = request.POST.get(f'question_{q.pk}', '')
            if answer == q.correct_option:
                score += 1

        percentage = round((score / total) * 100) if total > 0 else 0
        passed = percentage >= assessment.passing_score

        AssessmentSubmission.objects.create(
            assessment=assessment, student=request.user,
            score=score, total=total, passed=passed
        )

        if passed:
            messages.success(request, f'Congratulations! You passed with {percentage}%!')
        else:
            messages.warning(request, f'You scored {percentage}%. Required: {assessment.passing_score}%. Wait for faculty to create a new assessment.')
        return redirect('research:group_detail', pk=group.pk)

    return render(request, 'research/take_assessment.html', {
        'assessment': assessment, 'questions': questions, 'group': group
    })


@login_required
def assessment_results(request, assessment_pk):
    assessment = get_object_or_404(KnowledgeAssessment, pk=assessment_pk)
    group = assessment.group
    if request.user not in [group.supervisor, group.co_supervisor]:
        messages.error(request, 'Only supervisors can view results.')
        return redirect('research:group_detail', pk=group.pk)

    submissions = assessment.submissions.all()
    return render(request, 'research/assessment_results.html', {
        'assessment': assessment, 'submissions': submissions, 'group': group
    })


@login_required
def advance_to_study(request, pk):
    group = get_object_or_404(ResearchGroup, pk=pk)
    if request.user not in [group.supervisor, group.co_supervisor]:
        messages.error(request, 'Only supervisor or co-supervisor can advance the phase.')
        return redirect('research:group_detail', pk=pk)
    if group.all_assessments_passed():
        group.status = 'paper_study'
        group.save()
        messages.success(request, 'All members passed! Group advanced to Paper Study phase.')
    else:
        messages.error(request, 'Not all members have passed the assessment yet.')
    return redirect('research:group_detail', pk=pk)


# ==================== REFERENCE PAPERS ====================
@login_required
def add_reference_paper(request, pk):
    group = get_object_or_404(ResearchGroup, pk=pk)
    if request.user not in [group.supervisor, group.co_supervisor]:
        messages.error(request, 'Only supervisors can add reference papers.')
        return redirect('research:group_detail', pk=pk)

    if request.method == 'POST':
        form = ReferencePaperForm(request.POST)
        if form.is_valid():
            rp = form.save(commit=False)
            rp.group = group
            rp.added_by = request.user
            rp.save()
            messages.success(request, 'Reference paper added!')
            return redirect('research:group_detail', pk=pk)
    else:
        form = ReferencePaperForm()
    return render(request, 'research/add_reference.html', {'form': form, 'group': group})


@login_required
def advance_to_writing(request, pk):
    group = get_object_or_404(ResearchGroup, pk=pk)
    if request.user not in [group.supervisor, group.co_supervisor]:
        messages.error(request, 'Only supervisors can advance the phase.')
        return redirect('research:group_detail', pk=pk)
    group.status = 'paper_writing'
    group.save()
    messages.success(request, 'Group advanced to Paper Writing phase!')
    return redirect('research:group_detail', pk=pk)


# ==================== RESEARCH PAPER ====================
@login_required
def submit_paper(request, pk):
    group = get_object_or_404(ResearchGroup, pk=pk)
    if request.user not in group.members.all():
        messages.error(request, 'Only group members can submit papers.')
        return redirect('research:group_detail', pk=pk)

    revision_paper = group.papers.filter(status='revision').order_by('-updated_at').first()

    if request.method == 'POST':
        form = ResearchPaperForm(request.POST, request.FILES)
        if form.is_valid():
            if revision_paper:
                revision_paper.title = form.cleaned_data['title']
                revision_paper.abstract = form.cleaned_data['abstract']
                revision_paper.document = form.cleaned_data['document']
                revision_paper.submitted_by = request.user
                revision_paper.status = 'submitted'
                revision_paper.save()

                revision_paper.reviews.all().delete()

                messages.success(request, 'Revised paper submitted for review!')
            else:
                p = form.save(commit=False)
                p.group = group
                p.submitted_by = request.user
                p.status = 'submitted'
                p.save()
                messages.success(request, 'Paper submitted for review!')

            group.status = 'evaluation'
            group.save()
            return redirect('research:group_detail', pk=pk)
    else:
        if revision_paper:
            form = ResearchPaperForm(instance=revision_paper)
        else:
            form = ResearchPaperForm()

    return render(request, 'research/submit_paper.html', {'form': form, 'group': group})


@login_required
def review_paper(request, paper_pk):
    paper = get_object_or_404(ResearchPaper, pk=paper_pk)
    group = paper.group
    if request.user not in [group.supervisor, group.co_supervisor]:
        messages.error(request, 'Only supervisors can review papers.')
        return redirect('research:group_detail', pk=group.pk)

    existing = PaperReview.objects.filter(paper=paper, reviewer=request.user).first()
    if existing:
        messages.info(request, 'You already reviewed this paper.')
        return redirect('research:group_detail', pk=group.pk)

    if request.method == 'POST':
        form = PaperReviewForm(request.POST)
        if form.is_valid():
            r = form.save(commit=False)
            r.paper = paper
            r.reviewer = request.user
            r.save()

            if not r.is_approved:
                paper.status = 'revision'
                paper.save()

                group.status = 'paper_writing'
                group.save()

                messages.info(request, 'Paper marked for revision. Student can now correct and resubmit.')
            else:
                if paper.is_approved_by_both():
                    paper.status = 'approved'
                    paper.save()
                    messages.success(request, 'Paper approved by both reviewers!')
                else:
                    messages.success(request, 'Review submitted. Waiting for other reviewer.')
            return redirect('research:group_detail', pk=group.pk)
    else:
        form = PaperReviewForm()
    return render(request, 'research/review_paper.html', {
        'form': form, 'paper': paper, 'group': group
    })


@login_required
def publish_paper(request, paper_pk):
    paper = get_object_or_404(ResearchPaper, pk=paper_pk)
    group = paper.group
    if request.user not in [group.supervisor, group.co_supervisor]:
        messages.error(request, 'Only supervisors can publish.')
        return redirect('research:group_detail', pk=group.pk)

    if paper.is_approved_by_both():
        paper.status = 'published'
        paper.save()
        group.status = 'published'
        group.save()
        messages.success(request, 'Paper published successfully! Congratulations!')
    else:
        messages.error(request, 'Paper must be approved by both reviewers first.')
    return redirect('research:group_detail', pk=group.pk)
