from django.urls import path
from . import views

app_name = 'materials'

urlpatterns = [
    path('', views.material_semesters, name='semesters'),

    path('semester/<str:semester>/', views.material_courses_by_semester, name='semester_courses'),
    path('semester/<str:semester>/course/<str:course_name>/', views.materials_by_course, name='course_materials'),

    path('create/', views.material_create, name='create'),
    path('pending/', views.material_pending, name='pending'),

    path('<int:pk>/', views.material_detail, name='detail'),
    path('<int:pk>/edit/', views.material_edit, name='edit'),
    path('<int:pk>/delete/', views.material_delete, name='delete'),
    path('<int:pk>/download/', views.material_download, name='download'),
    path('<int:pk>/approve/', views.material_approve, name='approve'),
]