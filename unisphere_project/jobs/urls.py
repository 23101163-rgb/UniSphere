from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [

    path('', views.job_list, name='list'),
    path('create/', views.job_create, name='create'),


    path('pending/', views.job_pending, name='pending'),
    path('bookmarks/', views.my_bookmarks, name='bookmarks'),


    path('<int:pk>/bookmark/', views.job_bookmark, name='bookmark'),
    path('<int:pk>/verify/', views.job_verify, name='verify'),
    path('<int:pk>/apply/', views.job_apply, name='apply'),


    path('<int:pk>/', views.job_detail, name='detail'),
]
