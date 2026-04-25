from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from .forms import RegisterForm, LoginForm, ProfileUpdateForm
from .models import User
from notifications.utils import create_notification
from research.models import ResearchGroup, ResearchPaper


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()

            # ✅ Notify admins/teachers if registered as club member
            if user.is_club_member:
                admins_teachers = User.objects.filter(role__in=['admin', 'teacher'])
                for staff in admins_teachers:
                    create_notification(
                        recipient=staff,
                        title='New Club Verification Request',
                        message=f'{user.get_full_name()} registered as a club member in "{user.get_club_display()}" ({user.get_club_position_display()}). Please verify.',
                        link='/accounts/club-verification/'
                    )

            login(request, user)
            messages.success(request, 'Sign up successful! Welcome to UniLink.')
            return redirect('accounts:dashboard')
        else:
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
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            return redirect('accounts:dashboard')
        else:
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
    old_club = request.user.is_club_member
    old_club_name = request.user.club_name
    old_club_position = request.user.club_position

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()

            # ✅ Notify admins/teachers if new or changed club membership
            new_club = request.user.is_club_member
            new_club_name = request.user.club_name
            if new_club and (not old_club or old_club_name != new_club_name or old_club_position != request.user.club_position):
                admins_teachers = User.objects.filter(role__in=['admin', 'teacher'])
                for staff in admins_teachers:
                    create_notification(
                        recipient=staff,
                        title='New Club Verification Request',
                        message=f'{request.user.get_full_name()} requested club membership in "{request.user.get_club_display()}" as "{request.user.get_club_position_display()}". Please verify.',
                        link='/accounts/club-verification/'
                    )

            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
        else:
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
    """Teacher/Admin sees pending club verification requests"""
    if not request.user.is_teacher() and not request.user.is_admin_user():
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')

    pending_members = User.objects.filter(is_club_member=True, is_club_verified=False).order_by('-created_at')
    verified_members = User.objects.filter(is_club_member=True, is_club_verified=True).order_by('-created_at')

    return render(request, 'accounts/club_verification.html', {
        'pending_members': pending_members,
        'verified_members': verified_members,
    })


@login_required
def verify_club_member(request, pk):
    """Approve a club member"""
    if not request.user.is_teacher() and not request.user.is_admin_user():
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')

    member = get_object_or_404(User, pk=pk)
    member.is_club_verified = True
    member.save()

    create_notification(
        recipient=member,
        title='Club Membership Verified!',
        message=f'Your membership in "{member.get_club_display()}" as "{member.get_club_position_display()}" has been verified by {request.user.get_full_name()}.',
        link='/accounts/profile/'
    )

    messages.success(request, f'{member.get_full_name()} has been verified as a club member.')
    return redirect('accounts:club_verification')


@login_required
def reject_club_member(request, pk):
    """Reject a club member request"""
    if not request.user.is_teacher() and not request.user.is_admin_user():
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')

    member = get_object_or_404(User, pk=pk)
    member.is_club_member = False
    member.is_club_verified = False
    member.club_name = ''
    member.club_position = ''
    member.save()

    create_notification(
        recipient=member,
        title='Club Membership Rejected',
        message=f'Your club membership request has been rejected by {request.user.get_full_name()}. Please contact the club authority for more info.',
        link='/accounts/profile/'
    )

    messages.info(request, f'{member.get_full_name()} club membership has been rejected.')
    return redirect('accounts:club_verification')