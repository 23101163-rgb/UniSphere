from django.urls import path
from . import views

app_name = 'thesis'

urlpatterns = [
    path('', views.thesis_list, name='list'),
    path('create/', views.thesis_create, name='create'),
    path('<int:pk>/', views.thesis_detail, name='detail'),
    path('mentors/', views.mentor_list, name='mentors'),
    path('mentors/<int:mentor_pk>/request/', views.send_mentorship_request, name='send_request'),
    path('my-requests/', views.my_mentorship_requests, name='my_requests'),
    path('request/<int:pk>/<str:action>/', views.handle_mentorship_request, name='handle_request'),
    path('groups/', views.research_group_list, name='groups'),
    path('groups/create/', views.research_group_create, name='group_create'),
    path('groups/<int:pk>/join/', views.research_group_join, name='group_join'),
]
