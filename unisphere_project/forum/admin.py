from django.contrib import admin
from .models import Category, Thread, Reply

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'author', 'is_pinned', 'is_flagged', 'created_at']
    list_filter = ['category', 'is_flagged', 'is_pinned']

@admin.register(Reply)
class ReplyAdmin(admin.ModelAdmin):
    list_display = ['thread', 'author', 'is_flagged', 'created_at']

