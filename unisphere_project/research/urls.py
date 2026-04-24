from django.urls import path
from . import views

app_name = 'research'

urlpatterns = [
    # --- Research Groups ---
    path('groups/', views.research_group_list, name='groups'),
    path('groups/create/', views.research_group_create, name='group_create'),
    path('groups/<int:pk>/', views.group_detail, name='group_detail'),
    path('groups/<int:pk>/join/', views.research_group_join, name='group_join'),
    path('groups/<int:pk>/leave/', views.research_group_leave, name='group_leave'),

    # --- Open Group Join Request ---
    path('join-request/<int:request_pk>/approve/', views.approve_join_request, name='approve_join_request'),
    path('join-request/<int:request_pk>/decline/', views.decline_join_request, name='decline_join_request'),

    # --- Closed Group Invitation ---
    path('groups/<int:pk>/send-invitation/', views.send_group_invitation, name='send_group_invitation'),
    path('invitation/<int:invitation_pk>/accept/', views.accept_group_invitation, name='accept_group_invitation'),
    path('invitation/<int:invitation_pk>/decline/', views.decline_group_invitation, name='decline_group_invitation'),

    # --- Supervisor Request ---
    path('groups/<int:pk>/request-supervisor/', views.request_supervisor, name='request_supervisor'),
    path('supervisor-requests/', views.my_supervisor_requests, name='my_supervisor_requests'),
    path('supervisor-request/<int:pk>/<str:action>/', views.handle_supervisor_request, name='handle_supervisor_request'),

    # --- Co-Supervisor Request ---
    path('groups/<int:pk>/request-cosupervisor/', views.request_cosupervisor, name='request_cosupervisor'),

    # --- Topic Selection ---
    path('groups/<int:pk>/select-topic/', views.select_topic, name='select_topic'),

    # --- Knowledge Assessment ---
    path('groups/<int:pk>/create-assessment/', views.create_assessment, name='create_assessment'),
    path('assessment/<int:assessment_pk>/add-question/', views.add_question, name='add_question'),
    path('assessment/<int:assessment_pk>/take/', views.take_assessment, name='take_assessment'),
    path('assessment/<int:assessment_pk>/results/', views.assessment_results, name='assessment_results'),
    path('groups/<int:pk>/advance-to-study/', views.advance_to_study, name='advance_to_study'),

    # --- Reference Papers ---
    path('groups/<int:pk>/add-reference/', views.add_reference_paper, name='add_reference'),
    path('groups/<int:pk>/advance-to-writing/', views.advance_to_writing, name='advance_to_writing'),

    # --- Research Paper ---
    path('groups/<int:pk>/submit-paper/', views.submit_paper, name='submit_paper'),
    path('paper/<int:paper_pk>/review/', views.review_paper, name='review_paper'),
    path('paper/<int:paper_pk>/publish/', views.publish_paper, name='publish_paper'),
]