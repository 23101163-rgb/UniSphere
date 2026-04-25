from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('', views.event_list, name='list'),
    path('create/', views.event_create, name='create'),
    path('pending/', views.event_pending, name='pending'),
    path('club/<str:club_name>/', views.club_events, name='club_events'),
    path('<int:pk>/register/', views.event_register, name='register'),
    path('<int:pk>/approve/', views.event_approve, name='approve'),
    path('<int:pk>/reject/', views.event_reject, name='reject'),
    path('<int:pk>/', views.event_detail, name='detail'),
    path('my-events/', views.my_events, name='my_events'),
    path('participants/<int:pk>/', views.event_participants, name='participants'),
]