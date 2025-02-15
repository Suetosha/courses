from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Prefetch
from django.shortcuts import redirect
from django.urls import reverse_lazy

from django.views.generic import TemplateView, ListView, FormView, UpdateView, DeleteView, CreateView

from courses_apps.courses.forms import *
from courses_apps.courses.models import Course, Category, Chapter, Content, Test, Task, TestTask
from courses_apps.utils.mixins import TitleMixin


class HomeTemplateView(TitleMixin, TemplateView):
    template_name = "courses/students/home.html"
    title = "Курсы"

    def get(self, request, *args, **kwargs):
        context = super(HomeTemplateView, self).get_context_data(*args, **kwargs)
        query = request.GET.get("query", "").strip()
        category_id = request.GET.get("category")

        courses = Course.objects.filter(status="published")
        categories = Category.objects.all()

        if query:
            courses = Course.objects.filter(title__icontains=query)
        if category_id:
            courses = courses.filter(category_id=category_id)

        context['courses'] = courses
        context['categories'] = categories
        return self.render_to_response(context)


class CourseTemplateView(TitleMixin, TemplateView):
    template_name = "courses/students/course.html"
    title = "Страница курса"

    def get(self, request, *args, **kwargs):
        context = super(CourseTemplateView, self).get_context_data(*args, **kwargs)

        chapters = list(Chapter.objects.filter(course_id=kwargs["pk"]).order_by("id"))
        course = Course.objects.get(pk=kwargs["pk"])

        for chapter in chapters:
            tests = Test.objects.filter(chapter=chapter)
            chapter.completed_tests_count = sum(1 for test in tests if test.id in request.user.completed_tests)
            chapter.total_tests_count = tests.count()

        # Первая глава всегда доступна
        if chapters:
            chapters[0].is_accessible = True

        for i in range(1, len(chapters)):
            prev_chapter = chapters[i - 1]
            current_chapter = chapters[i]

            prev_tests = Test.objects.filter(chapter=prev_chapter)
            prev_completed_count = sum(1 for test in prev_tests if test.id in request.user.completed_tests)

            # Текущая глава доступна, если предыдущая полностью пройдена

            current_chapter.is_accessible = prev_completed_count == prev_tests.count()

        context['course'] = course
        context['chapters'] = chapters
        return self.render_to_response(context)


class ChapterTemplateView(TitleMixin, TemplateView):
    template_name = "courses/students/chapter.html"
    title = "Глава"

    def get(self, request, *args, **kwargs):
        context = super(ChapterTemplateView, self).get_context_data(*args, **kwargs)
        chapter = Chapter.objects.get(id=kwargs["pk"])

        try:
            content = Content.objects.get(chapter_id=kwargs["pk"])
            if content.text:
                context['text'] = content.text

            if content.video:
                context['video'] = content.video

            if content.files:
                context['file'] = content.files

        except Content.DoesNotExist:
            pass

        tests = Test.objects.filter(chapter_id=kwargs["pk"])

        context['chapter'] = chapter
        context['tasks'] = tests
        return self.render_to_response(context)


class TestTemplateView(TitleMixin, TemplateView):
    template_name = "courses/students/test.html"
    title = "Тест"
    form_class = AnswerForm

    def get(self, request, *args, **kwargs):
        context = super(TestTemplateView, self).get_context_data(*args, **kwargs)
        user = request.user

        test = Test.objects.get(id=kwargs["pk"])
        tests = Test.objects.filter(chapter_id=test.chapter_id)

        context['tasks'] = tests
        context['test'] = test

        if test.id in user.completed_tests:
            context["form"] = self.form_class(initial={"answer": test.correct_answer})
            context["form"].fields["answer"].widget.attrs["readonly"] = True
            context["completed"] = True
        else:
            context["form"] = self.form_class()

        return self.render_to_response(context)

    def post(self, request, **kwargs):
        form = AnswerForm(request.POST)
        if form.is_valid():
            test = Test.objects.get(id=kwargs["pk"])
            user = request.user

            user_answer = form.cleaned_data["answer"].lower()
            correct_answer = test.correct_answer.lower()

            if user_answer == correct_answer:
                messages.success(request, "Правильный ответ!")
                user.completed_tests.append(test.id)
                user.save(update_fields=["completed_tests"])

            else:
                messages.error(request, 'Неправильный ответ')

            return redirect("courses:test", pk=test.id)


#                              Курсы

# Просмотр курсов
class CoursesListView(TitleMixin, ListView):
    template_name = "courses/teachers/courses/courses_list.html"
    title = "Просмотр курсов"
    model = Course
    context_object_name = 'courses'


# Создание курсов
class CourseCreateView(TitleMixin, SuccessMessageMixin, FormView):
    title = "Создание курса"
    template_name = "courses/teachers/courses/create_course.html"
    form_class = CreateCourseForm
    model = Course
    success_url = reverse_lazy("courses:courses_list")
    success_message = "Курс успешно создан"

    def get_context_data(self, **kwargs):
        # Добавляем форму для глав в контекст
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['chapter_formset'] = ChapterFormSet(self.request.POST)
        else:
            context['chapter_formset'] = ChapterFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        chapter_formset = context['chapter_formset']

        # Сохраняем курс
        form.instance.save()

        if chapter_formset.is_valid():
            chapters = chapter_formset.save(commit=False)

            for chapter in chapters:
                # Привязка главы к курсу
                chapter.course = form.instance
                chapter.save()

        return super().form_valid(form)


# Редактирование курса
class CourseUpdateView(TitleMixin, SuccessMessageMixin, UpdateView):
    title = "Редактирование курса"
    template_name = "courses/teachers/courses/update_course.html"
    model = Course
    form_class = CreateCourseForm
    success_url = reverse_lazy("courses:courses_list")
    success_message = "Курс успешно обновлен"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        course_id = self.kwargs["pk"]
        course = Course.objects.get(id=course_id)
        chapters = Chapter.objects.filter(course=course)

        form = CreateCourseForm(instance=course)

        context['form'] = form
        context['chapters'] = chapters
        return context


# Удаление курса
class CourseDeleteView(TitleMixin, SuccessMessageMixin, DeleteView):
    title = "Удаление курса"
    template_name = "courses/teachers/courses/course_confirm_delete.html"
    model = Course
    success_url = reverse_lazy('courses:courses_list')
    success_message = "Курс успешно удален"


#                               Категории

# Создание категорий
class CategoryCreateView(TitleMixin, SuccessMessageMixin, CreateView):
    title = "Создание категории"
    template_name = "courses/teachers/create_category.html"
    form_class = CreateCategoryForm
    model = Category
    success_url = reverse_lazy('courses:courses_list')
    success_message = "Категория успешно создана"


#                               Главы

# Создание глав
class ChapterUpdateView(TitleMixin, SuccessMessageMixin, TemplateView):
    title = 'Редактирование главы'
    template_name = 'courses/teachers/update_chapter.html'


    def get_context_data(self, **kwargs):
        # Получаем объект главы
        chapter = Chapter.objects.get(id=self.kwargs['pk'])

        # Создаем формы
        chapter_form = ChapterForm(instance=chapter)
        content = Content.objects.filter(chapter=chapter).first()
        content_form = CreateContentForm(instance=content)

        # Передаем формы и объект главы в контекст
        context = {
            'form': chapter_form,
            'content_form': content_form,
            'chapter': chapter
        }
        return context

    def post(self, request, *args, **kwargs):
        chapter = Chapter.objects.get(id=self.kwargs['pk'])

        chapter_form = ChapterForm(request.POST, instance=chapter)
        content_form = CreateContentForm(request.POST, request.FILES)

        if 'update_chapter' in request.POST.dict() and chapter_form.is_valid():
            chapter_form.save()
            messages.success(request, 'Название главы успешно обновлено')
            return redirect(reverse_lazy('courses:edit_chapter', kwargs={'pk': chapter.id}))


        if 'update_content' in request.POST.dict() and content_form.is_valid():
            content, _ = Content.objects.get_or_create(chapter=chapter)

            content.text = content_form.cleaned_data.get('text')
            video = content_form.cleaned_data.get('video')
            files = content_form.cleaned_data.get('files')

            if 'video-clear' in request.POST:
                content.video = None
            if video:
                content.video = content_form.cleaned_data.get('video')

            if 'files-clear' in request.POST:
                content.files = None
            if files:
                content.files = video

            content.chapter = chapter
            content.save()

            messages.success(request, 'Контент главы успешно обновлен')
            return redirect(reverse_lazy('courses:edit_chapter', kwargs={'pk': chapter.id}))

        # Если хотя бы одна форма не валидна, возвращаем данные и ошибки
        context = self.get_context_data()
        context['form'] = chapter_form
        context['content_form'] = content_form

        return self.render_to_response(context)


#                                   Задания

# Просмотр заданий
class TaskListView(TitleMixin, ListView):
    title = "Просмотр заданий"
    template_name = "courses/teachers/tasks/tasks_list.html"
    model = Task
    context_object_name = 'tasks'

    def get_queryset(self):
        return Task.objects.prefetch_related("answer_set")


# Создание задания
class TaskCreateView(TitleMixin, SuccessMessageMixin, CreateView):
    title = 'Создание задания'
    template_name = "courses/teachers/tasks/create_task.html"
    model = Task
    form_class = CreateTaskForm
    success_url = reverse_lazy("courses:tasks_list")
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

            # Проходим по всем ответам и сохраняем их
            for answer in answers:
                answer.task = self.object  # Привязываем ответ к вопросу
                answer.save()

        return super().form_valid(form)


# Редактирование задания
class TaskUpdateView(TitleMixin, SuccessMessageMixin, UpdateView):
    title = 'Редактировать задание'
    model = Task
    template_name = "courses/teachers/tasks/update_task.html"
    form_class = CreateTaskForm
    success_url = reverse_lazy("courses:tasks_list")
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
class TaskDeleteView(TitleMixin, SuccessMessageMixin, DeleteView):
    title = 'Удалить задание'
    template_name = "courses/teachers/tasks/task_confirm_delete.html"
    model = Task
    success_url = reverse_lazy('courses:tasks_list')
    success_message = 'Задание успешно удалено'



#                                Тесты

# Просмотр тестов
class TestListView(TitleMixin, ListView):
    title = 'Просмотр тестов'
    template_name = 'courses/teachers/tests/tests_list.html'
    model = Chapter
    context_object_name = 'courses'

    def get_queryset(self):
        # Предзагрузка заданий через связь ManyToMany в Test
        tasks_prefetch = Prefetch(
            "tasks",  # Используем правильное имя поля ManyToMany - "tasks"
            queryset=Task.objects.all(),
            to_attr="prefetched_tasks"
        )

        # Предзагрузка тестов и их заданий
        tests_prefetch = Prefetch(
            "test_set",
            queryset=Test.objects.prefetch_related(tasks_prefetch),
            to_attr="prefetched_tests"
        )

        # Предзагрузка глав и их тестов
        chapters_prefetch = Prefetch(
            "chapter_set",
            queryset=Chapter.objects.prefetch_related(tests_prefetch),
            to_attr="prefetched_chapters"
        )

        # Получаем основной queryset с предзагруженными главами, тестами и заданиями
        queryset = Course.objects.prefetch_related(chapters_prefetch)

        return queryset

# Создание теста
class TestCreateView(TitleMixin, SuccessMessageMixin, CreateView):
    title = 'Создание теста'
    template_name = 'courses/teachers/tests/create_test.html'
    model = Test
    form_class = CreateTestForm
    success_url = reverse_lazy('courses:tests_list')
    success_message = 'Тест успешно создан'


    def form_valid(self, form):
        test = form.save()

        tasks = form.cleaned_data['tasks']
        # Используем set() для установки связи с задачами
        test.tasks.set(tasks)

        return super().form_valid(form)


# Удаление теста
class TestDeleteView(TitleMixin, SuccessMessageMixin, DeleteView):
    title = 'Удалить тест'
    template_name = "courses/teachers/tests/test_confirm_delete.html"
    model = Test
    success_url = reverse_lazy('courses:tests_list')
    success_message = 'Тест успешно удален'
