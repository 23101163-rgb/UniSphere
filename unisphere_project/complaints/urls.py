from django.urls import path
from . import views

app_name = 'complaints'

urlpatterns = [
    path('submit/', views.complaint_submit, name='submit'),
    path('my/', views.my_complaints, name='my_complaints'),
    path('<int:pk>/', views.complaint_detail, name='detail'),
    path('manage/', views.complaint_manage, name='manage'),
    path('teacher-manage/', views.teacher_complaint_manage, name='teacher_manage'),
    path('<int:pk>/respond/', views.complaint_respond, name='respond'),
]