from django.urls import path

from courses_apps.tests.views import *

app_name = 'tests'


urlpatterns = [
    #                     Задания
    path("tasks_list/", TaskListView.as_view(), name="tasks_list"),
    path("create_task/", TaskCreateView.as_view(), name="create_task"),
    path("edit_task/<int:pk>", TaskUpdateView.as_view(), name="edit_task"),
    path("delete_task/<int:pk>", TaskDeleteView.as_view(), name="delete_task"),

    #                     Тесты
    path("tests_list/", TestListView.as_view(), name="tests_list"),
    path("create_test/", TestCreateView.as_view(), name="create_test"),
    path("delete_test/<int:pk>", TestDeleteView.as_view(), name="delete_test"),
]