from django.urls import path
from courses_apps.courses.views import *

app_name = 'courses'



urlpatterns = [
    path("", HomeTemplateView.as_view(), name='home'),

    # Для студентов
    path("course/<int:course_id>", CourseTemplateView.as_view(), name='course'),
    path("course/<int:course_id>/chapter/<int:chapter_id>", ChapterTemplateView.as_view(), name='chapter'),
    path("course/<int:course_id>/chapter/<chapter_id>/task/<int:task_id>", TaskTemplateView.as_view(), name='task'),

    #               Для преподавателей

    #                     Курсы
    path("courses_list/", CoursesListView.as_view(), name='courses_list'),
    path("create_course/", CourseCreateView.as_view(), name="create_course"),
    path("edit_course/<int:pk>", CourseUpdateView.as_view(), name="edit_course"),
    path("delete_course/<int:pk>", CourseDeleteView.as_view(), name="delete_course"),

    #                     Категории
    path("create_category/", CategoryCreateView.as_view(), name="create_category"),
    path("delete_category/<int:pk>/", CategoryDeleteView.as_view(), name="delete_category"),

    #                     Главы
    path("edit_chapter/<int:pk>", ChapterUpdateView.as_view(), name="edit_chapter"),

    #                     Задания
    path("tasks_list/", TaskListView.as_view(), name="tasks_list"),
    path("create_task/", TaskCreateView.as_view(), name="create_task"),
    path("edit_task/<int:pk>", TaskUpdateView.as_view(), name="edit_task"),
    path("delete_task/<int:pk>", TaskDeleteView.as_view(), name="delete_task"),

    #                     Тесты
    path("tests_list/", TestListView.as_view(), name="tests_list"),
    path("create_test/", TestCreateView.as_view(), name="create_test"),
    path("delete_test/<int:pk>", TestDeleteView.as_view(), name="delete_test"),

    #                     Студенты
    path("students_list/", StudentListView.as_view(), name="students_list"),
    path("create_student/", StudentCreateView.as_view(), name="create_student"),
    path("delete_student/<int:pk>", StudentDeleteView.as_view(), name="delete_student"),

    #                     Подписки
    path("subscriptions/", SubscriptionListView.as_view(), name="subscriptions_list"),
    path("delete_subscription/<int:course_id>/<int:group_id>/",
         SubscriptionDeleteView.as_view(), name="subscription_delete"),

]