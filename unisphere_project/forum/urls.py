from django.urls import path
from . import views

app_name = 'forum'

urlpatterns = [
    path('', views.forum_home, name='home'),
    path('category/<slug:slug>/', views.category_threads, name='category'),
    path('thread/<int:pk>/', views.thread_detail, name='thread_detail'),
    path('thread/create/', views.thread_create, name='thread_create'),
    path('thread/<int:pk>/edit/', views.thread_edit, name='thread_edit'),
    path('thread/<int:pk>/delete/', views.thread_delete, name='thread_delete'),
    path('thread/<int:pk>/upvote/', views.upvote_thread, name='upvote'),
    path('reply/<int:pk>/upvote/', views.upvote_reply, name='upvote_reply'),
    path('flag/<str:content_type>/<int:pk>/', views.flag_content, name='flag'),
    path('search/', views.search_threads, name='search'),
]
