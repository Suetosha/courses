import os

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import StreamingHttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.db.models import Exists, OuterRef
from django.views import View

from django.views.generic import TemplateView, ListView, FormView, UpdateView, DeleteView, CreateView

from courses_apps.courses.forms import *
from courses_apps.courses.models import *
from courses_apps.tests.models import *
from courses_apps.users.models import CourseSubscription, ChapterProgress, TaskProgress
from courses_apps.utils.compiler import run_code
from courses_apps.utils.mixins import TitleMixin, RedirectTeacherMixin, RedirectStudentMixin, SubscriptionRequiredMixin, \
    ChapterAccessMixin


#                           Прохождение курсов - функционал для студентов

# Главная страница с курсами для студента
class HomeTemplateView(LoginRequiredMixin, RedirectTeacherMixin, TitleMixin, TemplateView):
    template_name = "courses/students/home.html"
    title = "Курсы"

    def get(self, request, *args, **kwargs):
        context = super(HomeTemplateView, self).get_context_data(*args, **kwargs)
        query = request.GET.get("query", "").strip()
        category_id = request.GET.get("category")

        courses = Course.objects.filter(status="published", coursesubscription__user=request.user)
        categories = Category.objects.all()

        if query:
            courses = Course.objects.filter(title__icontains=query)
        if category_id:
            courses = courses.filter(category_id=category_id)

        context['courses'] = courses
        context['categories'] = categories
        return self.render_to_response(context)


# Страница курса
class CourseTemplateView(LoginRequiredMixin, RedirectTeacherMixin, SubscriptionRequiredMixin, TitleMixin, TemplateView):
    template_name = "courses/students/course.html"
    title = "Страница курса"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        course = Course.objects.get(id=kwargs["course_id"])
        chapters = Chapter.objects.filter(course=course).order_by("id")
        subscription = CourseSubscription.objects.get(user=request.user, course=course)

        for chapter in chapters:
            test = Test.objects.filter(chapter=chapter).first()
            chapter_progress = ChapterProgress.objects.filter(chapter=chapter, subscription=subscription).first()

            if chapter_progress:
                # Подсчет общего количества заданий в главе
                chapter.total_tasks = test.tasks.count() if test else 0

                # Получение выполненных тестов по главе
                chapter.completed_tasks = TaskProgress.objects.filter(
                    chapter_progress=chapter_progress,
                ).count()

                chapter.is_completed = chapter_progress.is_completed

        # Определяем доступность глав
        for i, chapter in enumerate(chapters):
            if i == 0:
                # Первая глава будет доступна всегда
                chapter.is_accessible = True
            else:
                prev_chapter = chapters[i - 1]
                prev_chapter_progress = ChapterProgress.objects.filter(
                    subscription=subscription,
                    chapter=prev_chapter
                ).first()

                # Если предыдущая глава завершена, текущая становится доступной
                chapter.is_accessible = prev_chapter_progress.is_completed if prev_chapter_progress else False

        context['course'] = course
        context['chapters'] = chapters
        return self.render_to_response(context)


# Вью для обработки видео. Оптимизирует процесс путем деления видео на несколько частей
class VideoStreamView(View):
    def get(self, request, content_id, *args, **kwargs):
        content = get_object_or_404(Content, id=content_id)

        video_path = content.video.path

        def file_iterator(file_name, chunk_size=8192):
            with open(file_name, "rb") as f:
                while chunk := f.read(chunk_size):
                    yield chunk

        response = StreamingHttpResponse(file_iterator(video_path), content_type="video/mp4")
        response["Content-Disposition"] = f'inline; filename="{os.path.basename(video_path)}"'
        return response


# Страница главы
class ChapterTemplateView(LoginRequiredMixin, RedirectTeacherMixin, ChapterAccessMixin, TitleMixin, TemplateView):
    template_name = "courses/students/chapter.html"
    title = "Глава"

    def get(self, request, *args, **kwargs):
        context = super(ChapterTemplateView, self).get_context_data(*args, **kwargs)
        course_id = kwargs["course_id"]
        chapter_id = kwargs["chapter_id"]

        chapter = Chapter.objects.get(id=chapter_id)
        subscription = CourseSubscription.objects.get(user=request.user, course=course_id)

        # Создаем или получаем прогресс по главе
        chapter_progress, _ = ChapterProgress.objects.get_or_create(
            chapter=chapter, subscription=subscription)

        # Проверка на то, есть ли по данной главе тесты
        has_tests = Task.objects.filter(tests__chapter_id=chapter_id).exists()

        if not has_tests:
            chapter_progress.is_completed = True
            chapter_progress.save()


        # Добавляем к каждому заданию флаг is_completed=True, если он есть в TaskProgress
        tasks_in_chapter = Task.objects.filter(
            tests__chapter_id=chapter_id
        ).annotate(
            is_completed=Exists(
                TaskProgress.objects.filter(
                    chapter_progress=chapter_progress,
                    # OuterRef("id")- ссылка на внешний Task.id
                    test_task__task=OuterRef("id")
                )
            )
        )

        chapter_content = Content.objects.filter(chapter=chapter).first()

        context['chapter'] = chapter
        context['tasks'] = tasks_in_chapter
        context['chapter_content'] = chapter_content
        return self.render_to_response(context)


# Страница задания
class TaskTemplateView(LoginRequiredMixin, RedirectTeacherMixin, TitleMixin, TemplateView):
    template_name = "courses/students/task.html"
    title = "Задание"
    form_class = TaskAnswerForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_id, chapter_id, task_id = kwargs["course_id"], kwargs["chapter_id"], kwargs["task_id"]

        # Получение пользователя
        user = self.request.user

        # Получение прогресса по выполненным заданиям
        task_progress = TaskProgress.objects.filter(
            chapter_progress__subscription__user=user,
            chapter_progress__subscription__course=course_id,
            chapter_progress__chapter=chapter_id
        )

        # Добавляем флаг is_completed = True, если айди задания есть в task_progress
        tasks_in_chapter = (Task.objects.filter(tests__chapter_id=chapter_id)
                            .annotate(is_completed=Exists(task_progress.filter(test_task__task=OuterRef("id")))))

        # Получение текущего задания
        current_task = tasks_in_chapter.filter(id=task_id).first()

        # Получение всех и правильных вариантов ответа
        answers = Answer.objects.filter(task=current_task) if current_task else None
        correct_answers = answers.filter(is_correct=True) if answers else None

        context.update({
            "current_task": current_task,
            "is_task_completed": current_task.is_completed if current_task else False,
            "tasks_in_chapter": tasks_in_chapter,
            "answers": answers,
            "course_id": course_id,
            "chapter_id": chapter_id,
            "task_id": task_id,
        })

        if "form" in kwargs:
            context["form"] = kwargs["form"]

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        # Если задание выполнено, заполняем форму ответами
        if context["current_task"] and context["current_task"].is_completed:
            current_task = context["current_task"]
            answers = context["answers"]
            correct_answers = answers.filter(is_correct=True) if answers else None

            if current_task.is_multiple_choice:
                selected_answers = [str(answer.id) for answer in correct_answers] if correct_answers else []
                form = TaskAnswerForm(task=current_task, answers=answers, initial={"answers": selected_answers})
            else:
                form = TaskAnswerForm(task=current_task, answers=answers,
                                      initial={"answers": correct_answers.first().text if correct_answers else ""})
                form["answers"].label = "Правильный ответ"

            # Делаем поля формы недоступными для редактирования
            for field in form.fields.values():
                field.widget.attrs["readonly"] = True
                field.widget.attrs["disabled"] = True
        else:
            form = TaskAnswerForm(task=context["current_task"], answers=context["answers"])

        context["form"] = form
        return self.render_to_response(context)

    def post(self, request, **kwargs):
        task = Task.objects.get(id=kwargs["task_id"])
        answers = Answer.objects.filter(task=task)
        form = self.form_class(task, answers, data=request.POST)

        if form.is_valid():
            # Правильные ответы или ответ
            answers = Answer.objects.filter(task=task, is_correct=True)

            # Ответ студента
            user_answers = form.cleaned_data["answers"]

            # Если задание с компилятором
            if task.is_compiler:
                code = form.cleaned_data["compiler"]
                user_answers = run_code(code)
                correct_answer = answers.first().text

            # Если задания с множественным выбором, то лучше сравнивать с помощью айди
            elif task.is_multiple_choice:
                correct_answer = [str(a.id) for a in answers]
                correct_answer = correct_answer[0] if len(correct_answer) == 1 else correct_answer

            # Если задание с полем ввода
            else:
                correct_answer = answers.first().text

            is_correct = (user_answers == correct_answer)

            if is_correct:
                # Обозначаем, что глава пройдена
                self._update_chapter_progress(request, **kwargs)

                form = self.form_class(task, answers, initial={
                    "compiler": code if task.is_compiler else None,
                    "answers": correct_answer
                })

                messages.success(request, "Правильный ответ!")

            else:
                messages.error(request, 'Неправильный ответ')

            context = self.get_context_data(form=form, **kwargs)
            return self.render_to_response(context)


    @staticmethod
    def _update_chapter_progress(request, **kwargs):
        task = Task.objects.get(id=kwargs["task_id"])
        chapter = Chapter.objects.get(id=kwargs["chapter_id"])

        # Получаем прогресс главы
        chapter_progress, _ = ChapterProgress.objects.get_or_create(
            subscription__user=request.user,
            subscription__course_id=kwargs['course_id'],
            chapter=chapter
        )

        # Добавляем выполненное задание в TaskProgress
        task_progress = TaskProgress(
            chapter_progress=chapter_progress,
            test_task=TestTask.objects.get(task=task, test=Test.objects.get(chapter=chapter))
        )
        task_progress.save()

        # Подсчет общего количества заданий в главе
        total_tasks = Test.objects.get(chapter=chapter).tasks.count()

        # Получение выполненных тестов по главе
        completed_tasks = chapter_progress.taskprogress_set.count()

        # Если все задания по данной главе пройдены, то она считается пройденной
        if total_tasks == completed_tasks:
            chapter_progress.is_completed = True
            chapter_progress.save()


#                              Курсы - Функционал для преподавателя

# Просмотр курсов
class CoursesListView(LoginRequiredMixin, RedirectStudentMixin, TitleMixin, ListView):
    template_name = "courses/teachers/courses_list.html"
    title = "Просмотр курсов"
    model = Course
    context_object_name = 'courses'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context


# Создание курсов
class CourseCreateView(LoginRequiredMixin, RedirectStudentMixin, TitleMixin, SuccessMessageMixin, FormView):
    title = "Создание курса"
    template_name = "courses/teachers/create_course.html"
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
class CourseUpdateView(LoginRequiredMixin, RedirectStudentMixin, TitleMixin, SuccessMessageMixin, UpdateView):
    title = "Редактирование курса"
    template_name = "courses/teachers/update_course.html"
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
class CourseDeleteView(LoginRequiredMixin, RedirectStudentMixin, TitleMixin, SuccessMessageMixin, DeleteView):
    title = "Удаление курса"
    template_name = "courses/teachers/course_confirm_delete.html"
    model = Course
    success_url = reverse_lazy('courses:courses_list')
    success_message = "Курс успешно удален"


#                               Категории - функционал для преподавателя

# Создание категорий
class CategoryCreateView(LoginRequiredMixin, RedirectStudentMixin, TitleMixin, SuccessMessageMixin, CreateView):
    title = "Создание категории"
    template_name = "courses/teachers/create_category.html"
    form_class = CreateCategoryForm
    model = Category
    success_url = reverse_lazy('courses:courses_list')
    success_message = "Категория успешно создана"


# Удалить категорию
class CategoryDeleteView(LoginRequiredMixin, RedirectStudentMixin, DeleteView):
    model = Category
    success_url = reverse_lazy('courses:courses_list')

    def get(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)


#                              Главы - функционал для преподавателя

# Создание глав
class ChapterUpdateView(LoginRequiredMixin, RedirectStudentMixin, TitleMixin, SuccessMessageMixin, TemplateView):
    title = 'Редактирование главы'
    template_name = 'courses/teachers/update_chapter.html'

    def get_context_data(self, **kwargs):
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
                content.video = video

            if 'files-clear' in request.POST:
                content.files = None
            if files:
                content.files = files

            content.chapter = chapter
            content.save()

            messages.success(request, 'Контент главы успешно обновлен')
            return redirect(reverse_lazy('courses:edit_chapter', kwargs={'pk': chapter.id}))

        # Если хотя бы одна форма не валидна, возвращаем данные и ошибки
        context = self.get_context_data()
        context['form'] = chapter_form
        context['content_form'] = content_form

        return self.render_to_response(context)


#                                Компилятор

class CompilerFormView(LoginRequiredMixin, TitleMixin, RedirectTeacherMixin, FormView):
    title = 'Компилятор'
    template_name = 'courses/students/compiler.html'
    form_class = CompilerForm

    def form_valid(self, form):
        context = self.get_context_data()
        form = context['form']
        if form.is_valid():
            code = form.cleaned_data["compiler"]
            output = run_code(code)
            return self.render_to_response(self.get_context_data(
                form=self.form_class(initial={"compiler": code, "answer": output})
            ))
