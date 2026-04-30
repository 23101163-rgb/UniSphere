from django.contrib import admin
from .models import Complaint
@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ['subject', 'category', 'status', 'is_anonymous', 'created_at']
    list_filter = ['status', 'category']
