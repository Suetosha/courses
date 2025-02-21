from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView

from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import *
from django.contrib.messages.views import SuccessMessageMixin

from courses_apps.users.models import *
from courses_apps.users.forms import *
from courses_apps.users.forms import UserLoginForm, UserProfileForm
from courses_apps.utils.add_students_excel import import_students_from_excel
from courses_apps.utils.generate_students_excel import generate_excel
from courses_apps.utils.mixins import TitleMixin, RedirectStudentMixin

#                             Пользователи

# Авторизация пользователя
class UserLoginView(TitleMixin, LoginView):
    template_name = 'users/login.html'
    form_class = UserLoginForm
    title = 'Авторизация'

    def get_success_url(self):
        user = self.request.user
        if user.is_superuser or user.role == "teacher":
            return reverse_lazy('courses:courses_list')
        return reverse_lazy('courses:home')


# Профиль пользователя с возможностью поменять пароль и посмотреть прогресс по курсам
class UserProfileView(LoginRequiredMixin, TitleMixin, SuccessMessageMixin, UpdateView):
    title = 'Профиль пользователя'
    model = User
    template_name = 'users/profile.html'
    form_class = UserProfileForm
    success_message = 'Вы успешно обновили пароль'


    def get_success_url(self):
        return reverse_lazy('users:profile', args=(self.object.id,))


    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, error)
        return super().form_invalid(form)


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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


#                                 Студенты

# Просмотр студентов + функционал создания эксель и добавление студентов через эксель
class StudentListView(LoginRequiredMixin, RedirectStudentMixin, TitleMixin, ListView):
    title = 'Список студентов'
    template_name = 'users/students_list.html'
    model = User
    context_object_name = 'students'

    def get_queryset(self):
        queryset = User.objects.filter(role="student").prefetch_related("groups")
        group_number = self.request.GET.get('group_number')
        year = self.request.GET.get('year')

        if group_number and year:
            group = Group.objects.filter(number=group_number, year=year).first()
            if group:
                queryset = queryset.filter(groups=group)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['group_form'] = GroupSearchForm(self.request.GET)
        context['import_form'] = ImportStudentsForm()
        return context

    def post(self, request, *args, **kwargs):

        # Если отправлен файл на добавление студентов
        if "excel_file" in request.FILES:
            import_form = ImportStudentsForm(request.POST, request.FILES)
            if import_form.is_valid():
                excel_file = request.FILES['excel_file']
                try:
                    import_students_from_excel(excel_file)
                    messages.success(request, "Студенты успешно загружены.")
                except Exception as e:
                    messages.error(request, f"Ошибка при загрузке: {str(e)}")
            else:
                messages.error(request, "Ошибка валидации файла.")
            return redirect("users:students_list")

        # Если отправлен запрос на экспорт студентов в Excel
        group_form = GroupSearchForm(request.POST)
        if group_form.is_valid():
            group = group_form.cleaned_data['groups']
            students = User.objects.filter(groups=group).exists()
            if not students:
                messages.error(request,"В данной группе нет студентов")
            elif group:
                return generate_excel(group.number, group.year)
            else:
                messages.error(request,"Группа не выбрана")

        return self.get(request, *args, **kwargs)


# Добавление студентов
class StudentCreateView(LoginRequiredMixin, RedirectStudentMixin, TitleMixin, SuccessMessageMixin, CreateView):
    title = 'Добавление студента'
    template_name = 'users/create_user.html'
    model = User
    form_class = CreateStudentForm
    success_url = reverse_lazy('users:students_list')
    success_message = 'Студент успешно добавлен'


# Удаление студента
class StudentDeleteView(LoginRequiredMixin, RedirectStudentMixin, TitleMixin, SuccessMessageMixin, DeleteView):
    title = 'Удалить студента'
    template_name = "users/student_confirm_delete.html"
    model = User
    success_url = reverse_lazy('users:students_list')
    success_message = 'Студент успешно удален'



#                         Подписки

# Просмотр подписок, их создание
class SubscriptionListView(LoginRequiredMixin, RedirectStudentMixin, TitleMixin, SuccessMessageMixin, ListView):
    title = "Подписки на курс"
    template_name = "users/subscription_list.html"
    model = Subscription

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = SubscriptionForm()

        # Загружаем все подписки с пользователями и их группами
        subscriptions = Subscription.objects.select_related('course', 'user').prefetch_related('user__groups')

        # Создаём словарь {course: [список групп]}
        course_groups = {}
        for sub in subscriptions:
            if sub.course not in course_groups:
                course_groups[sub.course] = set()
            course_groups[sub.course].update(sub.user.groups.all())

        context['subscriptions'] = {course: groups for course, groups in course_groups.items()}

        return context

    def post(self, request, *args, **kwargs):
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            # Создаем подписку
            course = form.cleaned_data['course']
            group = form.cleaned_data['group']

            students_by_group = User.objects.filter(groups=group)

            if students_by_group:
                for student in students_by_group:
                    if not Subscription.objects.filter(user=student, course=course).exists():
                        Subscription.objects.create(user=student, course=course)
                messages.success(request, 'Группа добавлена в курс')
            else:
                messages.error(request, 'В данной группе нет студентов')
            return redirect('users:subscriptions_list')


# Удаление подписки группы на курс
class SubscriptionDeleteView(LoginRequiredMixin, RedirectStudentMixin, TitleMixin, SuccessMessageMixin, View):
    title = 'Удалить подписку группы на курс'
    model = Subscription
    success_url = reverse_lazy('users:subscription_delete')
    success_message = 'Подписка группы на курс удалена'

    @staticmethod
    def get(request, course_id, group_id):
        users_in_group = User.objects.filter(groups__id=group_id)
        Subscription.objects.filter(course_id=course_id, user__in=users_in_group).delete()
        return redirect('users:subscriptions_list')


#                              Преподаватели

# Просмотр преподавателя
class TeachersListView(LoginRequiredMixin, RedirectStudentMixin, TitleMixin, ListView):
    title = "Список преподавателей"
    template_name = 'users/teachers_list.html'
    model = User
    context_object_name = 'teachers'

    def get_queryset(self):
        queryset = User.objects.filter(role="teacher")
        return queryset


# Добавление преподавателя
class TeacherCreateView(LoginRequiredMixin, RedirectStudentMixin, TitleMixin,  SuccessMessageMixin, CreateView):
    title = 'Добавление учителя'
    template_name = 'users/create_user.html'
    model = User
    form_class = CreateTeacherForm
    success_url = reverse_lazy('users:teachers_list')
    success_message = 'Преподаватель успешно добавлен'





