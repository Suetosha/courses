from django.contrib.auth.views import LogoutView
from django.urls import path

from courses_apps.users.views import *
from courses_apps.users.views import UserLoginView, UserProfileView

app_name = 'users'

urlpatterns = [
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('profile/<int:pk>', UserProfileView.as_view(), name='profile'),

    #                     Студенты
    path("students_list/", StudentListView.as_view(), name="students_list"),
    path("create_student/", StudentCreateView.as_view(), name="create_student"),
    path("delete_student/<int:pk>", StudentDeleteView.as_view(), name="delete_student"),

    #                     Подписки
    path("subscriptions/", SubscriptionListView.as_view(), name="subscriptions_list"),
    path("delete_subscription/<int:course_id>/<int:group_id>/",
         SubscriptionDeleteView.as_view(), name="subscription_delete"),

    #                    Преподаватели
    path("teachers/", TeachersListView.as_view(), name="teachers_list"),
    path("create_teacher/", TeacherCreateView.as_view(), name="create_teacher"),


]
