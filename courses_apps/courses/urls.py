from django.urls import path

from courses_apps.courses.views import HomeTemplateView, CourseTemplateView, ChapterTemplateView, TestTemplateView, \
    CoursesListView, CourseCreateView, CategoryCreateView, CourseEditView, CourseDeleteView, ChapterEditView

app_name = 'courses'



urlpatterns = [
    path("", HomeTemplateView.as_view(), name='home'),

    # Для студентов
    path("course/<int:pk>", CourseTemplateView.as_view(), name='course'),
    path("chapter/<int:pk>", ChapterTemplateView.as_view(), name='chapter'),
    path("tests/<int:pk>", TestTemplateView.as_view(), name='test'),

    # Для преподавателей
    path("courses_list/", CoursesListView.as_view(), name='courses_list'),
    path("create_course/", CourseCreateView.as_view(), name="create_course"),
    path("edit_course/<int:pk>", CourseEditView.as_view(), name="edit_course"),
    path("delete_course/<int:pk>", CourseDeleteView.as_view(), name="delete_course"),
    path("create_category/", CategoryCreateView.as_view(), name="create_category"),
    path("edit_chapter/<int:pk>", ChapterEditView.as_view(), name="edit_chapter"),
    # path("<int:pk>/add-tests/", AddTestsView.as_view(), name="add_tests"),

]