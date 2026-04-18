from django.contrib import admin
from .models import Event, EventRegistration
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'event_type', 'get_event_status', 'date', 'venue', 'created_by']
    list_filter = ['event_type']
@admin.register(EventRegistration)
class EventRegAdmin(admin.ModelAdmin):
    list_display = ['event', 'user', 'registered_at']