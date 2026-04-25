from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from notifications.utils import create_notification
from .models import Event, EventRegistration
from .forms import EventForm, EventRegistrationForm


@login_required
def event_list(request):
    today = timezone.localdate()

    if request.user.is_admin_user():
        club_events = Event.objects.filter(organizer_category='club')
        non_club_events = Event.objects.filter(organizer_category='non_club').order_by('date', 'time')
    else:
        club_events = Event.objects.filter(organizer_category='club', is_approved=True)
        non_club_events = Event.objects.filter(organizer_category='non_club', is_approved=True).order_by('date', 'time')

    club_cards = []
    for value, label in Event.CLUB_CHOICES:
        club_qs = club_events.filter(club_name=value)
        total_events = club_qs.count()
        upcoming_events = club_qs.filter(date__gte=today).count()

        if total_events > 0:
            club_cards.append({
                'value': value,
                'label': label,
                'total_events': total_events,
                'upcoming_events': upcoming_events,
            })

    return render(request, 'events/event_list.html', {
        'club_cards': club_cards,
        'non_club_events': non_club_events,
    })

@login_required
def club_events(request, club_name):
    if request.user.is_admin_user():
        events = Event.objects.filter(organizer_category='club', club_name=club_name)
    else:
        events = Event.objects.filter(organizer_category='club', club_name=club_name, is_approved=True)

    club_label = dict(Event.CLUB_CHOICES).get(club_name, club_name)

    return render(request, 'events/club_events.html', {
        'events': events.order_by('date', 'time'),
        'club_name': club_name,
        'club_label': club_label,
    })


@login_required
def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)

    # Block unapproved events from other students
    if not event.is_approved and event.created_by != request.user and not (request.user.is_admin_user() or request.user.is_teacher()):
        messages.error(request, 'This event is not yet approved.')
        return redirect('events:list')

    registration = EventRegistration.objects.filter(event=event, user=request.user).first()
    is_registered = registration is not None
    reg_count = event.registrations.count()

    return render(request, 'events/event_detail.html', {
        'event': event,
        'is_registered': is_registered,
        'registration': registration,
        'reg_count': reg_count,
    })


@login_required
def event_create(request):
    if not (request.user.is_teacher() or request.user.is_admin_user() or request.user.is_student()):
        messages.error(request, 'Only teacher, admin, or students can create events.')
        return redirect('events:list')

    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)

            # Club member student → auto assign their club
            if request.user.is_student() and request.user.is_club_member:
                if event.organizer_category == 'club':
                    event.club_name = request.user.club_name

            # Non-club event → clear club_name
            if event.organizer_category != 'club':
                event.club_name = ''

            event.created_by = request.user

            # Auto-approve logic:
            # Teacher/Admin → always auto-approved
            # Verified club member → auto-approved
            # Unverified club member / normal student → needs admin-teacher approval
            if (
                request.user.is_teacher() or
                request.user.is_admin_user() or
                (request.user.is_club_member and request.user.is_club_verified)
            ):
                event.is_approved = True
            else:
                event.is_approved = False

            event.save()

            # Notify admins/teachers if pending approval
            if not event.is_approved:
                from accounts.models import User
                staff = User.objects.filter(role__in=['admin', 'teacher'])
                for s in staff:
                    create_notification(
                        recipient=s,
                        title='New Event Needs Approval',
                        message=f'{request.user.get_full_name()} created an event "{event.title}". Please review and approve.',
                        link=f'/events/{event.pk}/'
                    )
                messages.success(request, 'Event created! It will be visible after admin/teacher approval.')
            else:
                messages.success(request, 'Event created successfully!')

            return redirect('events:detail', pk=event.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = EventForm()

    return render(request, 'events/event_form.html', {
        'form': form,
        'title': 'Create Event'
    })

@login_required
def event_register(request, pk):
    event = get_object_or_404(Event, pk=pk)

    if not event.is_approved and not (request.user == event.created_by or request.user.is_admin_user() or request.user.is_teacher()):
        messages.error(request, 'You cannot register for an unapproved event.')
        return redirect('events:list')

    existing_registration = EventRegistration.objects.filter(event=event, user=request.user).first()

    if event.get_event_status() == 'ended' and not existing_registration:
        messages.error(request, 'Registration is closed because this event has already ended.')
        return redirect('events:detail', pk=pk)

    if existing_registration:
        existing_registration.delete()
        messages.info(request, 'Registration cancelled.')
        return redirect('events:detail', pk=pk)

    if request.method == 'POST':
        form = EventRegistrationForm(request.POST, user=request.user)
        if form.is_valid():
            reg = form.save(commit=False)
            reg.event = event
            reg.user = request.user
            reg.save()

            messages.success(request, f'Registered for "{event.title}"!')

            create_notification(
                recipient=request.user,
                title='Event Registration Successful',
                message=f'You have successfully registered for "{event.title}"',
                link=f'/events/{event.pk}/'
            )

            if request.user != event.created_by:
                create_notification(
                    recipient=event.created_by,
                    title='New Event Registration',
                    message=f'{request.user.get_full_name() or request.user.username} registered for your event "{event.title}".',
                    link=f'/events/{event.pk}/'
                )

            return redirect('events:detail', pk=pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = EventRegistrationForm(user=request.user)

    return render(request, 'events/event_registration_form.html', {
        'form': form,
        'event': event,
    })


@login_required
def my_events(request):
    created_events = Event.objects.filter(created_by=request.user).order_by('-date')
    registered_events = Event.objects.filter(registrations__user=request.user).order_by('-date')

    return render(request, 'events/my_events.html', {
        'created_events': created_events,
        'registered_events': registered_events,
    })


@login_required
def event_participants(request, pk):
    event = get_object_or_404(Event, pk=pk)

    if not (request.user == event.created_by or request.user.is_admin_user() or request.user.is_teacher()):
        messages.error(request, "You are not allowed to view participants.")
        return redirect('events:detail', pk=pk)

    participants = EventRegistration.objects.filter(event=event).select_related('user')

    return render(request, 'events/event_participants.html', {
        'event': event,
        'participants': participants
    })


@login_required
def event_approve(request, pk):
    if not (request.user.is_admin_user() or request.user.is_teacher()):
        messages.error(request, 'Access denied.')
        return redirect('events:list')

    event = get_object_or_404(Event, pk=pk)
    event.is_approved = True
    event.save()

    create_notification(
        recipient=event.created_by,
        title='Event Approved!',
        message=f'Your event "{event.title}" has been approved by {request.user.get_full_name()} and is now visible to everyone.',
        link=f'/events/{event.pk}/'
    )

    messages.success(request, f'Event "{event.title}" has been approved.')
    return redirect('events:pending')


@login_required
def event_reject(request, pk):
    if not (request.user.is_admin_user() or request.user.is_teacher()):
        messages.error(request, 'Access denied.')
        return redirect('events:list')

    event = get_object_or_404(Event, pk=pk)

    create_notification(
        recipient=event.created_by,
        title='Event Rejected',
        message=f'Your event "{event.title}" has been rejected by {request.user.get_full_name()}.',
        link='/events/'
    )

    event.delete()
    messages.info(request, 'Event has been rejected and removed.')
    return redirect('events:pending')


@login_required
def event_pending(request):
    if not (request.user.is_admin_user() or request.user.is_teacher()):
        messages.error(request, 'Access denied.')
        return redirect('events:list')

    pending_events = Event.objects.filter(is_approved=False).order_by('-created_at')

    return render(request, 'events/event_pending.html', {
        'pending_events': pending_events,
    })