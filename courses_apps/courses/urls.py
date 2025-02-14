from django.urls import path

from courses_apps.courses.views import HomeTemplateView, CourseTemplateView, ChapterTemplateView, TestTemplateView, \
    CoursesListView, CourseCreateView, CategoryCreateView, CourseUpdateView, CourseDeleteView, ChapterUpdateView, \
    TaskCreateView, TaskUpdateView, TaskListView, TaskDeleteView

app_name = 'courses'



urlpatterns = [
    path("", HomeTemplateView.as_view(), name='home'),

    # Для студентов
    path("course/<int:pk>", CourseTemplateView.as_view(), name='course'),
    path("chapter/<int:pk>", ChapterTemplateView.as_view(), name='chapter'),
    path("tasks/<int:pk>", TestTemplateView.as_view(), name='test'),

    # Для преподавателей

    #                     Курсы
    path("courses_list/", CoursesListView.as_view(), name='courses_list'),
    path("create_course/", CourseCreateView.as_view(), name="create_course"),
    path("edit_course/<int:pk>", CourseUpdateView.as_view(), name="edit_course"),
    path("delete_course/<int:pk>", CourseDeleteView.as_view(), name="delete_course"),

    #                     Категории
    path("create_category/", CategoryCreateView.as_view(), name="create_category"),

    #                     Главы
    path("edit_chapter/<int:pk>", ChapterUpdateView.as_view(), name="edit_chapter"),

    #                     Задания
    path("tasks_list/", TaskListView.as_view(), name="tasks_list"),
    path("create_task/", TaskCreateView.as_view(), name="create_task"),
    path("edit_task/<int:pk>", TaskUpdateView.as_view(), name="edit_task"),
    path("delete_task/<int:pk>", TaskDeleteView.as_view(), name="delete_task"),





]