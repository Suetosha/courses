from django.urls import path

from courses_apps.courses.views import HomeTemplateView

app_name = 'courses'

urlpatterns = [
    path("", HomeTemplateView.as_view(), name='home'),

]