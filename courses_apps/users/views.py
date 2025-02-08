from django.contrib.auth.views import LoginView
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView
from django.contrib import messages
from courses_apps.users.forms import UserLoginForm, UserRegistrationForm
from courses_apps.users.models import User
from courses_apps.utils.mixins import TitleMixin
from django.contrib.messages.views import SuccessMessageMixin

class UserLoginView(TitleMixin, LoginView):
    template_name = 'users/login.html'
    form_class = UserLoginForm
    title = 'Авторизация'


class UserRegistrationView(TitleMixin, SuccessMessageMixin, CreateView):
    template_name = 'users/registration.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('users:login')
    success_message = 'Вы успешно зарегистрировались'
    title = 'Регистрация'

    def post(self, request, *args, **kwargs):
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Вы успешно зарегистрировались')
            return HttpResponseRedirect(reverse_lazy('users:login'))
        else:
            return HttpResponseBadRequest("Некорректные данные")


class UserProfileView(TitleMixin, TemplateView):
    title = 'Профиль'
    model = User
    template_name = 'users/profile.html'



