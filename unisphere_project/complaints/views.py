from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Complaint
from .forms import ComplaintForm, ComplaintResponseForm
from notifications.utils import create_notification

@login_required
def complaint_submit(request):
    if request.method == 'POST':
        form = ComplaintForm(request.POST)
        if form.is_valid():
            c = form.save(commit=False)
            c.submitted_by = request.user
            c.save()

            # ✅ Notify the target
            submitter_name = 'Anonymous' if c.is_anonymous else request.user.get_full_name()

            if c.target_type == 'teacher' and c.target_teacher:
                # Notify specific teacher
                create_notification(
                    recipient=c.target_teacher,
                    title='New Complaint Received',
                    message=f'{submitter_name} submitted a complaint: "{c.subject}".',
                    link=f'/complaints/{c.pk}/'
                )
            else:
                # Notify all admins
                from accounts.models import User
                admins = User.objects.filter(role='admin')
                for admin_user in admins:
                    create_notification(
                        recipient=admin_user,
                        title='New Complaint Received',
                        message=f'{submitter_name} submitted a complaint: "{c.subject}".',
                        link=f'/complaints/{c.pk}/'
                    )

            messages.success(request, 'Complaint submitted successfully.')
            return redirect('complaints:my_complaints')
    else:
        form = ComplaintForm()
    return render(request, 'complaints/complaint_form.html', {'form': form})

@login_required
def my_complaints(request):
    complaints = Complaint.objects.filter(submitted_by=request.user)
    return render(request, 'complaints/my_complaints.html', {'complaints': complaints})

@login_required
def complaint_detail(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk)
    # Allow: submitter, admin, or target teacher
    if (complaint.submitted_by != request.user
        and not request.user.is_admin_user()
        and complaint.target_teacher != request.user):
        messages.error(request, 'Access denied.')
        return redirect('complaints:my_complaints')
    return render(request, 'complaints/complaint_detail.html', {'complaint': complaint})

@login_required
def complaint_manage(request):
    if not request.user.is_admin_user():
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    # Admin sees only admin-targeted complaints
    complaints = Complaint.objects.filter(target_type='admin')
    status_filter = request.GET.get('status', '')
    if status_filter:
        complaints = complaints.filter(status=status_filter)
    return render(request, 'complaints/complaint_manage.html', {'complaints': complaints})

@login_required
def teacher_complaint_manage(request):
    """Teachers see complaints directed to them"""
    if not request.user.is_teacher():
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    complaints = Complaint.objects.filter(target_teacher=request.user)
    status_filter = request.GET.get('status', '')
    if status_filter:
        complaints = complaints.filter(status=status_filter)
    return render(request, 'complaints/complaint_manage.html', {
        'complaints': complaints,
        'is_teacher_view': True,
    })

@login_required
def complaint_respond(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk)

    # Allow admin OR target teacher to respond
    if not request.user.is_admin_user() and complaint.target_teacher != request.user:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = ComplaintResponseForm(request.POST, instance=complaint)
        if form.is_valid():
            form.save()

            # ✅ Notify the complaint submitter
            status_display = complaint.get_status_display()
            responder = 'Admin' if request.user.is_admin_user() else request.user.get_full_name()
            notif_message = f'Your complaint "{complaint.subject}" status updated to "{status_display}" by {responder}.'
            if complaint.admin_response:
                notif_message += f' Response: {complaint.admin_response}'

            create_notification(
                recipient=complaint.submitted_by,
                title=f'Complaint Update: {complaint.subject}',
                message=notif_message,
                link=f'/complaints/{complaint.pk}/'
            )

            messages.success(request, 'Response updated.')
            if request.user.is_admin_user():
                return redirect('complaints:manage')
            return redirect('complaints:teacher_manage')
    else:
        form = ComplaintResponseForm(instance=complaint)
    return render(request, 'complaints/complaint_respond.html', {'form': form, 'complaint': complaint})