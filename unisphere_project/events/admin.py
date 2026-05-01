from django.contrib import admin
from .models import Event, EventRegistration
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'event_type', 'organizer_category', 'club_name', 'get_event_status', 'date', 'venue', 'created_by', 'is_approved']
    list_filter = ['event_type', 'organizer_category', 'club_name', 'is_approved']
@admin.register(EventRegistration)
class EventRegAdmin(admin.ModelAdmin):
    list_display = ['event', 'user', 'registered_at']
