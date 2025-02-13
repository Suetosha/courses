
# from django.contrib import admin
from django.urls import path
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include('courses_apps.courses.urls')),
    path('users/', include('courses_apps.users.urls'))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

