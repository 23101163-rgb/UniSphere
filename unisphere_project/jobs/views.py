from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import JobListing, JobBookmark,JobApplication
from .forms import JobListingForm,JobApplicationForm
from django.utils.timezone import now
from notifications.utils import create_notification

@login_required
def job_list(request):
    jobs = JobListing.objects.filter(is_verified=True)
    query = request.GET.get('q', '').strip()
    job_type = request.GET.get('type', '').strip()

    if query:
        jobs = jobs.filter(
            Q(title__icontains=query) |
            Q(company_name__icontains=query) |
            Q(required_skills__icontains=query)
        )

    if job_type:
        jobs = jobs.filter(job_type=job_type)

    jobs = jobs.order_by('-created_at')

    current_date = now().date()
    for job in jobs:
        if job.application_deadline >= current_date:
            job.status = 'running'
        else:
            job.status = 'ended'

    bookmarked_ids = JobBookmark.objects.filter(user=request.user).values_list('job_id', flat=True)

    return render(request, 'jobs/job_list.html', {
        'jobs': jobs,
        'query': query,
        'job_type': job_type,
        'bookmarked_ids': list(bookmarked_ids),
    })
from django.utils.timezone import now

@login_required
def job_detail(request, pk):
    job = get_object_or_404(JobListing, pk=pk)

    if not job.is_verified and job.posted_by != request.user and not (request.user.is_teacher() or request.user.is_admin_user()):
        messages.error(request, 'This job is not verified yet.')
        return redirect('jobs:list')

    is_bookmarked = JobBookmark.objects.filter(user=request.user, job=job).exists()
    has_applied = JobApplication.objects.filter(applicant=request.user, job=job).exists()

    # 🔥 status logic
    current_date = now().date()
    if job.application_deadline >= current_date:
        job.status = "running"
    else:
        job.status = "ended"

    return render(request, 'jobs/job_detail.html', {
        'job': job,
        'is_bookmarked': is_bookmarked,
        'has_applied': has_applied,
    })
@login_required
def job_create(request):
    if request.method == 'POST':
        form = JobListingForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.posted_by = request.user
            job.is_verified = request.user.is_admin_user()
            job.save()
            messages.success(request, 'Job posted!' + ('' if job.is_verified else ' Awaiting admin verification.'))
            return redirect('jobs:list')
    else:
        form = JobListingForm()
    return render(request, 'jobs/job_form.html', {'form': form})

@login_required
def job_bookmark(request, pk):
    job = get_object_or_404(JobListing, pk=pk)
    bm, created = JobBookmark.objects.get_or_create(user=request.user, job=job)
    if not created:
        bm.delete()
        messages.info(request, 'Bookmark removed.')
    else:
        messages.success(request, 'Job bookmarked!')
    return redirect('jobs:detail', pk=pk)

@login_required
def my_bookmarks(request):
    bookmarks = JobBookmark.objects.filter(user=request.user).select_related('job')
    return render(request, 'jobs/my_bookmarks.html', {'bookmarks': bookmarks})

@login_required
def job_apply(request, pk):
    job = get_object_or_404(JobListing, pk=pk)

    if not job.is_verified:
        messages.error(request, 'You cannot apply to an unverified job.')
        return redirect('jobs:list')

    existing_application = JobApplication.objects.filter(job=job, applicant=request.user).first()
    if existing_application:
        messages.info(request, 'You have already applied for this job.')
        return redirect('jobs:detail', pk=job.pk)

    if request.method == 'POST':
        form = JobApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.applicant = request.user
            application.save()

            messages.success(request, 'Your application was submitted successfully.')


            create_notification(
                user=request.user,
                title="Job Application Submitted",
                message=f'You applied for "{job.title}" at {job.company_name}',
                link=f'/jobs/{job.pk}/'
            )


            if request.user != job.posted_by:
                create_notification(
                    user=job.posted_by,
                    title="New Job Application",
                    message=f'{request.user.get_full_name() or request.user.username} applied for your job "{job.title}"',
                    link=f'/jobs/{job.pk}/'
                )

            return redirect('jobs:detail', pk=job.pk)
    else:
        form = JobApplicationForm(initial={
            'full_name': request.user.get_full_name(),
            'email': request.user.email,
            'phone': getattr(request.user, 'phone', '')
        })

    return render(request, 'jobs/job_apply_form.html', {
        'job': job,
        'form': form,
    })

@login_required
def job_pending(request):
    if not request.user.is_admin_user():
        messages.error(request, 'Access denied.')
        return redirect('jobs:list')
    jobs = JobListing.objects.filter(is_verified=False)
    return render(request, 'jobs/job_pending.html', {'jobs': jobs})
@login_required
def job_verify(request, pk):
    if not request.user.is_admin_user():
        messages.error(request, 'Access denied.')
        return redirect('jobs:list')

    job = get_object_or_404(JobListing, pk=pk)


    if job.is_verified:
        messages.info(request, 'This job is already verified.')
        return redirect('jobs:pending')

    job.is_verified = True
    job.save()


    if job.posted_by != request.user:
        create_notification(
            user=job.posted_by,
            title='Job Verified',
            message=f'Your job "{job.title}" has been verified and is now live.',
            link=f'/jobs/{job.pk}/'
        )


    create_notification(
        user=request.user,
        title='Job Verified',
        message=f'You verified "{job.title}"',
        link=f'/jobs/{job.pk}/'
    )

    messages.success(request, f'"{job.title}" verified successfully.')
    return redirect('jobs:pending')