from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    # List & Create
    path('', views.job_list, name='list'),
    path('create/', views.job_create, name='create'),

    # General pages
    path('pending/', views.job_pending, name='pending'),
    path('bookmarks/', views.my_bookmarks, name='bookmarks'),

    # Actions (specific আগে)
    path('<int:pk>/bookmark/', views.job_bookmark, name='bookmark'),
    path('<int:pk>/verify/', views.job_verify, name='verify'),
    path('<int:pk>/apply/', views.job_apply, name='apply'),

    # Detail (সবচেয়ে শেষে)
    path('<int:pk>/', views.job_detail, name='detail'),
]