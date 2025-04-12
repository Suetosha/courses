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

    #                     Контрольные тесты
    # Список контрольных тестов
    path('control_tests/', ControlTestListView.as_view(), name='control_tests_list'),

    # Просмотр конкретного контрольного теста
    path('control_tests/<int:control_test_id>/', ViewControlTestView.as_view(), name='view_control_test'),

    # Добавление задания в контрольный тест
    path('control_test/<int:control_test_id>/add_task/', AddTaskToControlTestView.as_view(),
         name='create_control_task'),

    # Обновление задания в контрольном тесте
    path("update_control_task/<int:pk>/", ControlTaskUpdateView.as_view(), name="update_control_task"),

    # Удаление контрольного теста
    path("delete_control_test/<int:pk>/", ControlTestDeleteView.as_view(), name="delete_control_test"),

]
