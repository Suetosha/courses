import os

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.files.storage import FileSystemStorage
from django.db.models import Prefetch
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, UpdateView, DeleteView, CreateView

from courses_apps.courses.forms import *
from courses_apps.tests.forms import *
from courses_apps.tests.models import *
from courses_apps.utils.add_tasks_excel import import_tasks_from_excel

from courses_apps.utils.mixins import TitleMixin, RedirectStudentMixin


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
        self.object = self.get_object()  # Получаем задание
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

