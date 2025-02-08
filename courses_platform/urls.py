
# from django.contrib import admin
from django.urls import path
from django.urls import path, include

urlpatterns = [
    path('', include('courses_apps.courses.urls')),
    path('users/', include('courses_apps.users.urls'))
]
