from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from .forms import RegisterForm, LoginForm, ProfileUpdateForm
from .models import User, ClubMembership
from notifications.utils import create_notification
from research.models import ResearchGroup, ResearchPaper


def get_user_display_name(user):
    return user.get_full_name() or user.username


def sync_user_club_status(user):
    """
    Keep old User club fields working as fallback,
    while the new ClubMembership table handles multiple clubs.
    """
    all_memberships = user.club_memberships.all().order_by('created_at')
    verified_memberships = all_memberships.filter(is_verified=True)

    first_membership = all_memberships.first()
    first_verified_membership = verified_memberships.first()

    user.is_club_member = all_memberships.exists()
    user.is_club_verified = verified_memberships.exists()

    if first_verified_membership:
        user.club_name = first_verified_membership.club_name
        user.club_position = first_verified_membership.club_position
    elif first_membership:
        user.club_name = first_membership.club_name
        user.club_position = first_membership.club_position
    else:
        user.club_name = ''
        user.club_position = ''

    user.save(update_fields=[
        'is_club_member',
        'is_club_verified',
        'club_name',
        'club_position',
    ])


def notify_staff_about_club_membership(user, memberships, action_text='registered as'):
    admins_teachers = User.objects.filter(role__in=['admin', 'teacher'])

    for membership in memberships:
        for staff in admins_teachers:
            create_notification(
                recipient=staff,
                title='New Club Verification Request',
                message=(
                    f'{get_user_display_name(user)} {action_text} '
                    f'"{membership.get_club_name_display()}" '
                    f'({membership.get_club_position_display()}). Please verify.'
                ),
                link='/accounts/club-verification/'
            )


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST, request.FILES)

        if form.is_valid():
            user = form.save()

            if user.is_club_member:
                pending_memberships = ClubMembership.objects.filter(
                    user=user,
                    is_verified=False
                )

                notify_staff_about_club_membership(
                    user=user,
                    memberships=pending_memberships,
                    action_text='registered as a club member in'
                )

            login(request, user)
            messages.success(request, 'Sign up successful! Welcome to UnisPhere.')
            return redirect('accounts:dashboard')

        messages.error(request, 'Please correct the errors below.')

    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(
                request,
                f'Welcome back, {get_user_display_name(user)}!'
            )
            return redirect('accounts:dashboard')

        messages.error(request, 'Wrong username/email or password.')

    else:
        form = LoginForm(request)

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')


@login_required
def dashboard_view(request):
    published_papers_count = 0
    supervised_papers_count = 0
    co_supervised_papers_count = 0
    supervising_groups = ResearchGroup.objects.none()
    co_supervising_groups = ResearchGroup.objects.none()

    if request.user.role in ['student', 'alumni']:
        published_papers_count = ResearchPaper.objects.filter(
            group__members=request.user,
            status='published'
        ).distinct().count()

    if request.user.role == 'teacher':
        supervising_groups = ResearchGroup.objects.filter(
            supervisor=request.user
        ).order_by('-created_at')

        co_supervising_groups = ResearchGroup.objects.filter(
            co_supervisor=request.user
        ).exclude(
            supervisor=request.user
        ).order_by('-created_at')

        supervised_papers_count = ResearchPaper.objects.filter(
            group__supervisor=request.user,
            status='published'
        ).distinct().count()

        co_supervised_papers_count = ResearchPaper.objects.filter(
            group__co_supervisor=request.user,
            status='published'
        ).distinct().count()

    context = {
        'user': request.user,
        'published_papers_count': published_papers_count,
        'supervised_papers_count': supervised_papers_count,
        'co_supervised_papers_count': co_supervised_papers_count,
        'supervising_groups': supervising_groups,
        'co_supervising_groups': co_supervising_groups,
    }

    return render(request, 'accounts/dashboard.html', context)


@login_required
def profile_view(request, pk=None):
    if pk:
        user = get_object_or_404(User, pk=pk)
    else:
        user = request.user

    published_papers_count = 0
    supervised_papers_count = 0
    co_supervised_papers_count = 0

    if user.role in ['student', 'alumni']:
        published_papers_count = ResearchPaper.objects.filter(
            group__members=user,
            status='published'
        ).distinct().count()

    if user.role == 'teacher':
        supervised_papers_count = ResearchPaper.objects.filter(
            group__supervisor=user,
            status='published'
        ).distinct().count()

        co_supervised_papers_count = ResearchPaper.objects.filter(
            group__co_supervisor=user,
            status='published'
        ).distinct().count()

    return render(request, 'accounts/profile.html', {
        'profile_user': user,
        'published_papers_count': published_papers_count,
        'supervised_papers_count': supervised_papers_count,
        'co_supervised_papers_count': co_supervised_papers_count,
    })


@login_required
def profile_edit_view(request):
    old_club_memberships = {
        membership.club_name: membership.club_position
        for membership in ClubMembership.objects.filter(user=request.user)
    }

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)

        if form.is_valid():
            user = form.save()

            pending_memberships = ClubMembership.objects.filter(
                user=user,
                is_verified=False
            )

            changed_or_new_pending_memberships = []

            for membership in pending_memberships:
                old_position = old_club_memberships.get(membership.club_name)

                if old_position != membership.club_position:
                    changed_or_new_pending_memberships.append(membership)

            if changed_or_new_pending_memberships:
                notify_staff_about_club_membership(
                    user=user,
                    memberships=changed_or_new_pending_memberships,
                    action_text='requested club membership in'
                )

            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')

        messages.error(request, 'Please correct the errors below.')

    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(request, 'accounts/profile_edit.html', {'form': form})


@login_required
def alumni_directory_view(request):
    alumni_list = User.objects.filter(role='alumni').order_by('-graduation_year')
    query = request.GET.get('q', '').strip()

    if query:
        alumni_list = alumni_list.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(company__icontains=query) |
            Q(expertise__icontains=query) |
            Q(username__icontains=query) |
            Q(email__icontains=query)
        )

    return render(request, 'accounts/alumni_directory.html', {
        'alumni_list': alumni_list,
        'query': query
    })


@login_required
def user_management_view(request):
    if not request.user.is_admin_user():
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')

    users = User.objects.all().order_by('-created_at')
    return render(request, 'accounts/user_management.html', {'users': users})


@login_required
def club_verification_requests(request):
    """
    Teacher/Admin sees club-wise pending verification requests.
    One user can have multiple club requests.
    Each ClubMembership is verified separately.
    """
    if not request.user.is_teacher() and not request.user.is_admin_user():
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')

    pending_memberships = ClubMembership.objects.select_related('user').filter(
        is_verified=False
    ).order_by('-created_at')

    verified_memberships = ClubMembership.objects.select_related('user').filter(
        is_verified=True
    ).order_by('-created_at')

    return render(request, 'accounts/club_verification.html', {
        'pending_memberships': pending_memberships,
        'verified_memberships': verified_memberships,
    })


@login_required
def verify_club_member(request, pk):
    """
    Approve one club membership request.
    pk = ClubMembership id, not User id.
    """
    if not request.user.is_teacher() and not request.user.is_admin_user():
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')

    membership = get_object_or_404(
        ClubMembership.objects.select_related('user'),
        pk=pk
    )

    membership.is_verified = True
    membership.authorized_to_post = True
    membership.save(update_fields=['is_verified', 'authorized_to_post'])

    member = membership.user
    sync_user_club_status(member)

    create_notification(
        recipient=member,
        title='Club Membership Verified!',
        message=(
            f'Your membership in "{membership.get_club_name_display()}" '
            f'as "{membership.get_club_position_display()}" has been verified by '
            f'{get_user_display_name(request.user)}.'
        ),
        link='/accounts/profile/'
    )

    messages.success(
        request,
        f'{get_user_display_name(member)} has been verified for '
        f'{membership.get_club_name_display()}.'
    )

    return redirect('accounts:club_verification')


@login_required
def reject_club_member(request, pk):
    """
    Reject one club membership request.
    pk = ClubMembership id, not User id.
    """
    if not request.user.is_teacher() and not request.user.is_admin_user():
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')

    membership = get_object_or_404(
        ClubMembership.objects.select_related('user'),
        pk=pk
    )

    member = membership.user
    club_name_display = membership.get_club_name_display()
    club_position_display = membership.get_club_position_display()

    membership.delete()
    sync_user_club_status(member)

    create_notification(
        recipient=member,
        title='Club Membership Rejected',
        message=(
            f'Your club membership request for "{club_name_display}" '
            f'as "{club_position_display}" has been rejected by '
            f'{get_user_display_name(request.user)}. Please contact the club authority for more info.'
        ),
        link='/accounts/profile/'
    )

    messages.info(
        request,
        f'{get_user_display_name(member)} club membership request for '
        f'{club_name_display} has been rejected.'
    )

    return redirect('accounts:club_verification')