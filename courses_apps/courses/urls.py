from django.urls import path
from courses_apps.courses.views import *

app_name = 'courses'

urlpatterns = [

    #                 Для студентов

    path("", HomeTemplateView.as_view(), name='home'),
    path("course/<int:course_id>", CourseTemplateView.as_view(), name='course'),
    path("video/<int:content_id>/", VideoStreamView.as_view(), name="video-stream"),
    path("course/<int:course_id>/chapter/<int:chapter_id>", ChapterTemplateView.as_view(), name='chapter'),
    path("course/<int:course_id>/chapter/<chapter_id>/task/<int:task_id>", TaskTemplateView.as_view(), name='task'),
    path("compiler/", CompilerFormView.as_view(), name='compiler'),

    #               Для преподавателей

    #                     Курсы
    path("courses_list/", CoursesListView.as_view(), name='courses_list'),
    path("create_course/", CourseCreateView.as_view(), name="create_course"),
    path("edit_course/<int:pk>", CourseUpdateView.as_view(), name="edit_course"),
    path("delete_course/<int:pk>", CourseDeleteView.as_view(), name="delete_course"),
    path("courses/<int:pk>/copy/", CourseCopyView.as_view(), name="course_copy"),

    #                     Категории
    path("create_category/", CategoryCreateView.as_view(), name="create_category"),
    path("delete_category/<int:pk>/", CategoryDeleteView.as_view(), name="delete_category"),

    #                     Главы
    path("edit_chapter/<int:pk>", ChapterUpdateView.as_view(), name="edit_chapter"),

]
