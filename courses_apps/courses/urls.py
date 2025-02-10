from django.urls import path

from courses_apps.courses.views import HomeTemplateView, CourseTemplateView, ChapterTemplateView, TestTemplateView

app_name = 'courses'

urlpatterns = [
    path("", HomeTemplateView.as_view(), name='home'),
    path("course/<int:pk>", CourseTemplateView.as_view(), name='course'),
    path("chapter/<int:pk>", ChapterTemplateView.as_view(), name='chapter'),
    path("tests/<int:pk>", TestTemplateView.as_view(), name='test'),
]