from django.contrib import admin
from .models import StudyMaterial, MaterialRating

@admin.register(StudyMaterial)
class StudyMaterialAdmin(admin.ModelAdmin):
    list_display = ['title', 'course_name', 'semester', 'uploaded_by', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'semester', 'course_name']
    search_fields = ['title', 'course_name', 'topic']

@admin.register(MaterialRating)
class MaterialRatingAdmin(admin.ModelAdmin):
    list_display = ['material', 'user', 'score', 'created_at']

