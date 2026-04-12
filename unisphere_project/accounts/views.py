from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from .forms import RegisterForm, LoginForm, ProfileUpdateForm
from .models import User


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
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
    context = {'user': request.user}
    return render(request, 'accounts/dashboard.html', context)


@login_required
def profile_view(request, pk=None):
    if pk:
        user = get_object_or_404(User, pk=pk)
    else:
        user = request.user
    return render(request, 'accounts/profile.html', {'profile_user': user})


@login_required
def profile_edit_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
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