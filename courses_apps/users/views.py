from django.contrib.auth.views import LoginView
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView, UpdateView
from django.contrib import messages

from courses_apps.courses.models import Course, Chapter, Test
from courses_apps.users.forms import UserLoginForm, UserRegistrationForm, UserProfileForm
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
    title = 'Регистрация'

    def post(self, request, *args, **kwargs):
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Вы успешно зарегистрировались')
            return HttpResponseRedirect(reverse_lazy('users:login'))
        else:
            return HttpResponseBadRequest("Некорректные данные")


class UserProfileView(TitleMixin, SuccessMessageMixin, UpdateView):
    title = 'Профиль пользователя'
    model = User
    template_name = 'users/profile.html'
    form_class = UserProfileForm
    success_message = 'Вы успешно обновили данные'


    def get_success_url(self):
        return reverse_lazy('users:profile', args=(self.object.id,))


    def get_context_data(self, **kwargs):
        context = super(UserProfileView, self).get_context_data(**kwargs)

        courses = Course.objects.filter(subscription__user_id=self.request.user.id)

        context['courses'] = courses
        #
        # for course in courses:
        #     chapters = Chapter.objects.filter(course=course)
        #     course.total_chapters = chapters.count()
        #     for test in Test.objects.filter(course=course):

        return context



