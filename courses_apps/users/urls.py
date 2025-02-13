from django.contrib.auth.views import LogoutView
from django.urls import path

from courses_apps.users.views import UserLoginView, UserRegistrationView, UserProfileView

app_name = 'users'

urlpatterns = [
    path('login/', UserLoginView.as_view(), name='login'),
    path('registration/', UserRegistrationView.as_view(), name='registration'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('profile/<int:pk>', UserProfileView.as_view(), name='profile'),


]
