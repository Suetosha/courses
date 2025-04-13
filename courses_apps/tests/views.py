import os

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.files.storage import FileSystemStorage
from django.db.models import Prefetch, F
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, UpdateView, DeleteView, CreateView, FormView, TemplateView

from courses_apps.courses.forms import *
from courses_apps.tests.forms import *
from courses_apps.tests.models import *
from courses_apps.users.forms import SubscriptionControlTestForm
from courses_apps.users.models import ControlTestSubscription, User
from courses_apps.utils.add_tasks_excel import import_tasks_from_excel


from courses_apps.utils.mixins import TitleMixin, RedirectStudentMixin
from courses_apps.utils.test_result import calculate_test_result


#                                   Задания

# Просмотр заданий + функционал добавления заданий через эксель
class TaskListView(LoginRequiredMixin, RedirectStudentMixin, TitleMixin, ListView):
    title = "Просмотр заданий"
    template_name = "tests/tasks_list.html"
    model = Task
    context_object_name = 'tasks'

    def get_queryset(self):
        return Task.objects.prefetch_related("answer_set")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ImportTasksForm()
        return context

    def post(self, request, *args, **kwargs):
        form = ImportTasksForm(request.POST, request.FILES)

        if form.is_valid():
            excel_file = request.FILES['excel_file']

            # Сохраняем файл временно
            fs = FileSystemStorage()
            filename = fs.save(excel_file.name, excel_file)
            file_path = fs.path(filename)

            try:
                import_tasks_from_excel(file_path)
                messages.success(request, "Задания успешно загружены.")
            except Exception as e:
                messages.error(request, f"{str(e)}")

            # Удаляем временный файл после обработки
            if os.path.exists(file_path):
                os.remove(file_path)

            return redirect('tests:tasks_list')

        return self.get(request, *args, **kwargs)


# Создание задания
class TaskCreateView(LoginRequiredMixin, RedirectStudentMixin, TitleMixin, SuccessMessageMixin, CreateView):
    title = 'Создание задания'
    template_name = "tests/create_task.html"
    model = Task
    form_class = CreateTaskForm
    success_url = reverse_lazy("tests:tasks_list")
    success_message = 'Задание успешно создано'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['answer_formset'] = AnswerFormUpdateSet(self.request.POST)
        else:
            context['answer_formset'] = AnswerFormCreateSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        answer_formset = context['answer_formset']

        # Сохраняем вопрос
        self.object = form.save()

        if answer_formset.is_valid():
            answers = answer_formset.save(commit=False)

            if len(answers) == 1 and not self.object.is_compiler:
                self.object.is_text_input = True
            elif len(answers) > 1:
                self.object.is_multiple_choice = True

            self.object.save()

            # Проходим по всем ответам и сохраняем их
            for answer in answers:
                # Привязываем ответ к вопросу
                answer.task = self.object
                answer.save()

        return super().form_valid(form)


# Редактирование задания
class TaskUpdateView(LoginRequiredMixin, RedirectStudentMixin, TitleMixin, SuccessMessageMixin, UpdateView):
    title = 'Редактировать задание'
    model = Task
    template_name = "tests/update_task.html"
    form_class = CreateTaskForm
    success_url = reverse_lazy("tests:tasks_list")
    success_message = "Данные обновлены"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.method == 'GET':
            answer_formset = AnswerFormCreateSet(instance=self.object)
        else:
            answer_formset = AnswerFormUpdateSet(instance=self.object)

        task_form = CreateTaskForm(instance=self.object)
        context['answer_formset'] = answer_formset
        context['form'] = task_form
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        task_form = self.get_form()
        answer_formset = AnswerFormUpdateSet(request.POST, instance=self.object)

        if task_form.is_valid() and answer_formset.is_valid():
            task_form.save()
            answer_formset.save()
            return self.form_valid(task_form)

        context = self.get_context_data()
        context['form'] = task_form
        context['answer_formset'] = answer_formset
        return self.render_to_response(context)


# Удаление задания
class TaskDeleteView(LoginRequiredMixin, RedirectStudentMixin, DeleteView):
    model = Task
    success_url = reverse_lazy('tests:tasks_list')

    def get(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)


#                                Тесты

# Просмотр тестов
class TestListView(LoginRequiredMixin, RedirectStudentMixin, TitleMixin, ListView):
    title = 'Просмотр тестов'
    template_name = 'tests/tests_list.html'
    model = Chapter
    context_object_name = 'courses'

    def get_queryset(self):
        # Получение задач в тестах
        tasks_prefetch = Prefetch(
            "tasks",
            queryset=Task.objects.all(),
            to_attr="prefetched_tasks"
        )

        # Получение тестов и их заданий
        tests_prefetch = Prefetch(
            "test",
            queryset=Test.objects.prefetch_related(tasks_prefetch),
            to_attr="prefetched_test"
        )

        # Получение глав и их тестов
        chapters_prefetch = Prefetch(
            "chapter_set",
            queryset=Chapter.objects.prefetch_related(tests_prefetch),
            to_attr="prefetched_chapters"
        )

        # Получаем основной queryset с полученными главами, тестами и заданиями
        queryset = Course.objects.prefetch_related(chapters_prefetch)

        return queryset


# Создание теста
class TestCreateView(LoginRequiredMixin, RedirectStudentMixin, TitleMixin, SuccessMessageMixin, CreateView):
    title = 'Создание теста'
    template_name = 'tests/create_test.html'
    model = Test
    form_class = CreateTestForm
    success_url = reverse_lazy('tests:tests_list')
    success_message = 'Тест успешно создан'

    def form_valid(self, form):
        test = form.save()

        tasks = form.cleaned_data['tasks']
        # Формируем связь теста с задачами
        test.tasks.set(tasks)

        return super().form_valid(form)


# Удаление теста
class TestDeleteView(LoginRequiredMixin, RedirectStudentMixin, DeleteView):
    model = Test
    success_url = reverse_lazy('tests:tests_list')

    def get(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)


#                                   Контрольные тесты

# Главная страница по контрольным тестам
class ControlTestListView(TitleMixin, LoginRequiredMixin, ListView, RedirectStudentMixin):
    title = "Контрольное тестирование"
    template_name = "tests/control_tests_list.html"
    model = ControlTest
    context_object_name = 'control_tests'

    def get_queryset(self):
        return ControlTest.objects.all().order_by('-title')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subscriptions_form'] = SubscriptionControlTestForm()

        subscriptions = (
            ControlTestSubscription.objects
            .select_related('user', 'control_test')
            .filter(user__role='student')
            .annotate(
                group_year=F('user__groups__year'),
                group_number=F('user__groups__number')
            )
            .order_by('control_test__title', 'group_number', 'group_year', 'user__last_name', 'user__first_name')
            .distinct()
        )

        context['subscriptions'] = subscriptions

        context['tasks'] = Task.objects.filter(controltesttask__control_test__in=self.object_list)

        return context

    def post(self, request, *args, **kwargs):
        title = request.POST.get('title')
        group, control_test = request.POST.get('group'), request.POST.get('control_test')

        if title:
            control_test = ControlTest.objects.create(title=title)
            messages.success(request, 'Контрольный тест успешно создан')
            return redirect('tests:view_control_test', control_test_id=control_test.id)

        if group and control_test:
            students_by_group = User.objects.filter(groups=group)

            if students_by_group:
                for student in students_by_group:
                    if not ControlTestSubscription.objects.filter(user=student, control_test_id=control_test).exists():
                        ControlTestSubscription.objects.create(user=student, control_test_id=control_test)
                        messages.success(request, 'Группа добавлена в контрольный тест')
            else:
                messages.error(request, 'В данной группе нет студентов')
            return redirect('tests:control_tests_list')

        messages.error(request, "Ошибка при отправке формы, попробуйте ещё")
        return self.get(request, *args, **kwargs)


# Страница контрольного теста
class ViewControlTestView(TitleMixin, TemplateView, RedirectStudentMixin, LoginRequiredMixin):
    template_name = "tests/view_control_test.html"
    title = "Контрольный тест"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        control_test_id = self.kwargs.get("control_test_id")
        control_test = get_object_or_404(ControlTest, id=control_test_id)

        context['form'] = ControlTestTitleForm(instance=control_test)
        context['control_test'] = control_test
        context['tasks'] = Task.objects.filter(controltesttask__control_test=control_test)
        return context

    def post(self, request, *args, **kwargs):
        control_test_id = self.kwargs.get("control_test_id")
        control_test = get_object_or_404(ControlTest, id=control_test_id)
        form = ControlTestTitleForm(request.POST, instance=control_test)

        if form.is_valid():
            form.save()
            messages.success(request, "Вы успешно обновили название контрольного теста")
            return redirect('tests:view_control_test', control_test_id=control_test_id)

        context = self.get_context_data(**kwargs)
        context['form'] = form
        return self.render_to_response(context)

# Страница по добавлению задания в контрольный тест
class AddTaskToControlTestView(TitleMixin, SuccessMessageMixin, FormView, RedirectStudentMixin, LoginRequiredMixin):
    title = 'Добавление задания в контрольный тест'
    template_name = "tests/create_control_task.html"
    form_class = CreateControlTaskForm
    success_message = 'Задание успешно добавлено в контрольный тест'

    def get_success_url(self):
        control_test_id = self.kwargs.get("control_test_id")
        return reverse_lazy("tests:view_control_test", kwargs={"control_test_id": control_test_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        control_test_id = self.kwargs.get("control_test_id")
        control_test = get_object_or_404(ControlTest, id=control_test_id)

        context["control_test"] = control_test

        if self.request.POST:
            context['answer_formset'] = AnswerFormCreateSet(self.request.POST)
        else:
            context['answer_formset'] = AnswerFormCreateSet()

        return context

    def form_valid(self, form):
        context = self.get_context_data()
        control_test = context["control_test"]
        answer_formset = context['answer_formset']

        self.object = form.save(commit=False)
        if answer_formset.is_valid():
            self.object.save()
            answers = answer_formset.save(commit=False)

            if len(answers) == 1 and not self.object.is_compiler:
                self.object.is_text_input = True
            elif len(answers) > 1:
                self.object.is_multiple_choice = True

            self.object.save()
            for answer in answers:
                answer.task = self.object
                answer.save()

            ControlTestTask.objects.create(control_test=control_test, task=self.object)

        return super().form_valid(form)


# Удаление контрольного теста
class ControlTestDeleteView(LoginRequiredMixin, RedirectStudentMixin, DeleteView):
    model = ControlTest
    success_url = reverse_lazy('tests:control_tests_list')

    def get(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)


# Страница редактирования задания в контрольном тесте
class ControlTaskUpdateView(TitleMixin, UpdateView, RedirectStudentMixin, LoginRequiredMixin, SuccessMessageMixin):
    title = 'Редактирование контрольного задания'
    template_name = "tests/update_control_task.html"
    form_class = CreateControlTaskForm
    model = Task

    def get_success_url(self):
        control_task_id = self.kwargs.get("pk")
        control_test_task = get_object_or_404(ControlTestTask, task_id=control_task_id)
        control_test_id = control_test_task.control_test.id
        messages.success(self.request, "Контрольное задание успешно обновлено.")
        return reverse_lazy("tests:view_control_test", kwargs={"control_test_id": control_test_id})


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        control_test_task = ControlTestTask.objects.filter(task_id=self.kwargs.get("pk")).first()
        control_test = control_test_task.control_test
        answer_formset = AnswerFormCreateSet(instance=self.object)
        task_form = CreateControlTaskForm(instance=self.object)

        context['answer_formset'] = answer_formset
        context['control_test'] = control_test
        context['form'] = task_form
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        task_form = self.get_form()
        answer_formset = AnswerFormUpdateSet(request.POST, instance=self.object)

        if task_form.is_valid() and answer_formset.is_valid():
            task_form.save()
            answer_formset.save()
            return self.form_valid(task_form)

        context = self.get_context_data()
        context['form'] = task_form
        context['answer_formset'] = answer_formset
        return self.render_to_response(context)


class ControlTaskDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Task
    success_message = 'Задание успешно удалено'

    def get_success_url(self):
        control_test_id = self.object.controltesttask_set.first().control_test.id
        return reverse_lazy('tests:view_control_test', kwargs={'control_test_id': control_test_id})
    

#                         Контрольные тесты для студента    

# Главная страница с контрольными тестами
class StudentControlTestListView(LoginRequiredMixin, TitleMixin, ListView):
    title = "Мои контрольные тесты"
    template_name = "tests/student_control_tests.html"
    model = ControlTest
    context_object_name = 'student_control_tests'

    def get_queryset(self):
        control_tests = ControlTest.objects.filter(
            controltestsubscription__user=self.request.user
        ).distinct()
        return control_tests


# Страница с решением контрольного теста
class FillControlTestView(LoginRequiredMixin, TemplateView):
    template_name = "tests/fill_control_test.html"
    title = "Решение контрольного теста"
    form_classes = ControlTaskAnswerForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        control_test = get_object_or_404(ControlTest, pk=self.kwargs['pk'])

        # Получаем задания контрольного теста
        tasks = Task.objects.filter(controltesttask__control_test=control_test)

        # Создаём формы для каждого задания
        task_forms = []
        for task in tasks:
            answers = Answer.objects.filter(task=task)
            form = self.form_classes(task=task, answers=answers)
            task_forms.append((task, form))

        context["control_test"] = control_test
        context["task_forms"] = task_forms
        return context

    def post(self, request, *args, **kwargs):
        control_test = get_object_or_404(ControlTest, pk=self.kwargs['pk'])
        tasks = Task.objects.filter(controltesttask__control_test=control_test)

        user_answers = {}
        task_errors = []

        for task in tasks:
            task_id = str(task.id)
            # Получение ответов для формы
            answers = Answer.objects.filter(task=task)
            form = self.form_classes(data=request.POST, task=task, answers=answers)

            if form.is_valid():
                # print("form.data", form.data)
                if task.is_multiple_choice:
                    # Для проверки множественного выбора
                    user_answers[task_id] = form.data.getlist(task_id, None)
                else:
                    user_answers[task_id] = form.data.get(task_id, None)
            else:
                task_errors.append(task)

        # Если есть ошибки в данных формы
        if task_errors:
            messages.error(request, "Некоторые ответы заполнены некорректно. Попробуйте снова.")
            return self.render_to_response(self.get_context_data())

        # Подсчет результатов
        results = calculate_test_result(tasks, user_answers)

        # Получение результатов проверки
        score = results["total_score"]
        max_score = results["max_score"]
        score_percent = results["score_percent"]
        final_result = results["result"]

        # Передача сообщения пользователю
        messages.success(
            request,
            f"Тест завершён! Вы набрали {score} из {max_score} баллов "
            f"({score_percent:.2f}%). Итоговая оценка: {final_result}."
        )

        subscription = ControlTestSubscription.objects.filter(user=request.user, control_test=control_test).first()
        subscription.result = score_percent
        subscription.is_completed = True
        subscription.save(update_fields=['result'])

        # Редирект на страницу завершения
        return HttpResponseRedirect(reverse_lazy('tests:control_tests'))
