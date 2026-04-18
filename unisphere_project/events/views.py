from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from notifications.utils import create_notification
from .models import Event, EventRegistration
from .forms import EventForm


@login_required
def event_list(request):
    today = timezone.localdate()

    club_events = Event.objects.filter(organizer_category='club')
    non_club_events = Event.objects.filter(organizer_category='non_club').order_by('date', 'time')

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
    events = Event.objects.filter(
        organizer_category='club',
        club_name=club_name
    ).order_by('date', 'time')

    club_label = dict(Event.CLUB_CHOICES).get(club_name, club_name)

    return render(request, 'events/club_events.html', {
        'events': events,
        'club_name': club_name,
        'club_label': club_label,
    })


@login_required
def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    is_registered = EventRegistration.objects.filter(event=event, user=request.user).exists()
    reg_count = event.registrations.count()

    return render(request, 'events/event_detail.html', {
        'event': event,
        'is_registered': is_registered,
        'reg_count': reg_count,
    })


@login_required
def event_create(request):

    if not (
        request.user.is_teacher() or
        request.user.is_admin_user() or
        (request.user.is_student() and request.user.is_club_member)
    ):
        messages.error(request, 'Only teachers, admins, or club members can create events.')
        return redirect('events:list')

    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)


            if request.user.is_student():
                if not request.user.is_club_member:
                    messages.error(request, 'You are not allowed to create events.')
                    return redirect('events:list')

                if event.organizer_category != 'club':
                    messages.error(request, 'Students can only create club events.')
                    return redirect('events:list')


                event.club_name = request.user.club_name


            if event.organizer_category != 'club':
                event.club_name = ''

            event.created_by = request.user
            event.save()

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
    reg, created = EventRegistration.objects.get_or_create(event=event, user=request.user)

    if created:
        messages.success(request, f'Registered for "{event.title}"!')


        create_notification(
            user=request.user,
            title="Event Registration Successful",
            message=f'You have successfully registered for "{event.title}"',
            link=f'/events/{event.pk}/'
        )


        if request.user != event.created_by:
            create_notification(
                user=event.created_by,
                title='New Event Registration',
                message=f'{request.user.get_full_name() or request.user.username} registered for your event "{event.title}".',
                link=f'/events/{event.pk}/'
            )

    else:
        reg.delete()
        messages.info(request, 'Registration cancelled.')

    return redirect('events:detail', pk=pk)
@login_required
def my_events(request):

    created_events = Event.objects.filter(created_by=request.user).order_by('-date')


    registered_events = Event.objects.filter(
        registrations__user=request.user
    ).order_by('-date')

    return render(request, 'events/my_events.html', {
        'created_events': created_events,
        'registered_events': registered_events,
    })
@login_required
def event_participants(request, pk):
    event = get_object_or_404(Event, pk=pk)


    if not (
        request.user == event.created_by or
        request.user.is_admin_user() or
        request.user.is_teacher()
    ):
        messages.error(request, "You are not allowed to view participants.")
        return redirect('events:detail', pk=pk)

    participants = EventRegistration.objects.filter(event=event).select_related('user')

    return render(request, 'events/event_participants.html', {
        'event': event,
        'participants': participants
    })