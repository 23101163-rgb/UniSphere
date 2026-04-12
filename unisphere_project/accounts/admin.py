from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'university_id', 'is_active']
    list_filter = ['role', 'is_active', 'department']
    fieldsets = UserAdmin.fieldsets + (
        ('UniLink Info', {'fields': ('role', 'university_id', 'department', 'phone',
            'bio', 'profile_picture', 'semester', 'research_interests', 'expertise',
            'graduation_year', 'company', 'designation', 'is_mentor_available', 'email_verified')}),
    )
