from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, ClubMembership, TeacherCourseAssignment

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'university_id', 'teacher_course_name', 'is_active']
    list_filter = ['role', 'is_active', 'department']
    fieldsets = UserAdmin.fieldsets + (
        ('UniLink Info', {'fields': ('role', 'university_id', 'department', 'phone',
            'bio', 'profile_picture', 'semester', 'teacher_course_name', 'research_interests', 'expertise',
            'graduation_year', 'company', 'designation', 'is_mentor_available', 'email_verified')}),
    )


@admin.register(ClubMembership)
class ClubMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'club_name', 'club_position', 'is_verified', 'authorized_to_post']
    list_filter = ['club_name', 'is_verified', 'authorized_to_post']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'club_name']


@admin.register(TeacherCourseAssignment)
class TeacherCourseAssignmentAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'semester', 'course_name']
    list_filter = ['semester', 'course_name']
    search_fields = ['teacher__username', 'teacher__first_name', 'teacher__last_name', 'course_name']
