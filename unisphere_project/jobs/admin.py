from django.contrib import admin
from .models import JobListing
@admin.register(JobListing)
class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'company_name', 'job_type', 'posted_by', 'is_verified', 'application_deadline']
    list_filter = ['is_verified', 'job_type']
