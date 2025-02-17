from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from django.contrib.messages.views import SuccessMessageMixin

from courses_apps.courses.models import Course, Chapter, ChapterProgress, Subscription
from courses_apps.users.forms import UserLoginForm, UserRegistrationForm, UserProfileForm
from courses_apps.users.models import User
from courses_apps.utils.mixins import TitleMixin



class UserLoginView(TitleMixin, LoginView):
    template_name = 'users/login.html'
    form_class = UserLoginForm
    title = 'Авторизация'


class UserRegistrationView(TitleMixin, SuccessMessageMixin, CreateView):
    template_name = 'users/registration.html'
    form_class = UserRegistrationForm
    success_message = "Вы успешно зарегистрировались!"
    success_url = reverse_lazy('users:login')
    title = 'Регистрация'

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)


class UserProfileView(LoginRequiredMixin, TitleMixin, SuccessMessageMixin, UpdateView):
    title = 'Профиль пользователя'
    model = User
    template_name = 'users/profile.html'
    form_class = UserProfileForm
    success_message = 'Вы успешно обновили пароль'


    def get_success_url(self):
        return reverse_lazy('users:profile', args=(self.object.id,))


    def get_context_data(self, **kwargs):
        context = super(UserProfileView, self).get_context_data(**kwargs)
        courses = Course.objects.filter(subscription__user_id=self.request.user.id)

        for course in courses:

            course.total_chapters = Chapter.objects.filter(course=course).count()
            course.chapter_progress = ChapterProgress.objects.filter(
                subscription__course=course,
                is_completed=True
            ).count()

        context['courses'] = courses
        return context



