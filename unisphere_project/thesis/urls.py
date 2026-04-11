from django.urls import path
from . import views

app_name = 'thesis'

urlpatterns = [
    path('', views.home, name='home'),
]
