from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import ThesisResource, MentorshipRequest, ResearchGroup
from .forms import ThesisResourceForm, MentorshipRequestForm, ResearchGroupForm
from accounts.models import User

@login_required
def thesis_list(request):
    theses = ThesisResource.objects.all()
    query = request.GET.get('q', '')
    if query:
        theses = theses.filter(Q(title__icontains=query) | Q(research_area__icontains=query) | Q(authors__icontains=query))
    return render(request, 'thesis/thesis_list.html', {'theses': theses, 'query': query})

@login_required
def thesis_detail(request, pk):
    thesis = get_object_or_404(ThesisResource, pk=pk)
    return render(request, 'thesis/thesis_detail.html', {'thesis': thesis})

@login_required
def thesis_create(request):
    if request.method == 'POST':
        form = ThesisResourceForm(request.POST, request.FILES)
        if form.is_valid():
            t = form.save(commit=False)
            t.uploaded_by = request.user
            t.save()
            messages.success(request, 'Thesis resource added!')
            return redirect('thesis:list')
    else:
        form = ThesisResourceForm()
    return render(request, 'thesis/thesis_form.html', {'form': form})

@login_required
def mentor_list(request):
    mentors = User.objects.filter(is_mentor_available=True, role__in=['teacher', 'alumni'])
    query = request.GET.get('q', '')
    if query:
        mentors = mentors.filter(Q(first_name__icontains=query) | Q(research_interests__icontains=query) | Q(expertise__icontains=query))
    return render(request, 'thesis/mentor_list.html', {'mentors': mentors, 'query': query})

@login_required
def send_mentorship_request(request, mentor_pk):
    mentor = get_object_or_404(User, pk=mentor_pk)
    if request.method == 'POST':
        form = MentorshipRequestForm(request.POST)
        if form.is_valid():
            mr = form.save(commit=False)
            mr.student = request.user
            mr.mentor = mentor
            mr.save()
            messages.success(request, f'Mentorship request sent to {mentor.get_full_name()}!')
            return redirect('thesis:mentors')
    else:
        form = MentorshipRequestForm()
    return render(request, 'thesis/mentorship_request.html', {'form': form, 'mentor': mentor})

@login_required
def my_mentorship_requests(request):
    if request.user.role in ['teacher', 'alumni']:
        requests_list = MentorshipRequest.objects.filter(mentor=request.user).order_by('-created_at')
    else:
        requests_list = MentorshipRequest.objects.filter(student=request.user).order_by('-created_at')
    return render(request, 'thesis/my_requests.html', {'requests_list': requests_list})

@login_required
def handle_mentorship_request(request, pk, action):
    mr = get_object_or_404(MentorshipRequest, pk=pk, mentor=request.user)
    mr.status = action
    mr.save()
    messages.success(request, f'Request {action}.')
    return redirect('thesis:my_requests')

@login_required
def research_group_list(request):
    groups = ResearchGroup.objects.all()
    return render(request, 'thesis/group_list.html', {'groups': groups})

@login_required
def research_group_create(request):
    if request.method == 'POST':
        form = ResearchGroupForm(request.POST)
        if form.is_valid():
            g = form.save(commit=False)
            g.created_by = request.user
            g.save()
            g.members.add(request.user)
            messages.success(request, 'Research group created!')
            return redirect('thesis:groups')
    else:
        form = ResearchGroupForm()
    return render(request, 'thesis/group_form.html', {'form': form})

@login_required
def research_group_join(request, pk):
    group = get_object_or_404(ResearchGroup, pk=pk)
    group.members.add(request.user)
    messages.success(request, f'Joined "{group.name}"!')
    return redirect('thesis:groups')
