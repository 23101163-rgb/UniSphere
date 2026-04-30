from django.contrib import admin
from .models import ThesisResource, MentorshipRequest, ResearchGroup

@admin.register(ThesisResource)
class ThesisAdmin(admin.ModelAdmin):
    list_display = ['title', 'authors', 'year', 'research_area']
    list_filter = ['year', 'research_area']

@admin.register(MentorshipRequest)
class MentorshipAdmin(admin.ModelAdmin):
    list_display = ['student', 'mentor', 'status', 'created_at']
    list_filter = ['status']

@admin.register(ResearchGroup)
class ResearchGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'research_area', 'created_by']
