from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static

def home(request):
    return HttpResponse('UniSphere_project initial starter project is running.')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('accounts/', include('accounts.urls')),
    path('materials/', include('materials.urls')),
    path('thesis/', include('thesis.urls')),
    path('forum/', include('forum.urls')),
    path('jobs/', include('jobs.urls')),
    path('complaints/', include('complaints.urls')),
    path('events/', include('events.urls')),
    path('notifications/', include('notifications.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
