from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Prefetch
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View

from django.views.generic import TemplateView, ListView, FormView, UpdateView, DeleteView, CreateView

from courses_apps.courses.forms import *
from courses_apps.courses.models import *
from courses_apps.utils.generate_students_excel import generate_excel
from courses_apps.utils.mixins import TitleMixin


class HomeTemplateView(LoginRequiredMixin, TitleMixin, TemplateView):
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


class CourseTemplateView(LoginRequiredMixin, TitleMixin, TemplateView):
    template_name = "courses/students/course.html"
    title = "Страница курса"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        course_id = kwargs["course_id"]

        # Получаем курс
        course = Course.objects.get(id=course_id)
        # Получаем главы к этому курсу
        chapters = Chapter.objects.filter(course=course).order_by("id")

        # Получаем подписку пользователя на курс
        subscription = Subscription.objects.get(user=request.user, course=course)

        for chapter in chapters:
            test = Test.objects.filter(chapter=chapter).first()

            # Подсчет общего количества заданий в главе
            chapter.total_tasks = test.tasks.count() if test else 0

            # Подсчет количества выполненных заданий
            if subscription and test:
                chapter.completed_tasks_count = ChapterProgress.objects.filter(
                    subscription=subscription, chapter=chapter, is_completed=True
                ).count()
            else:
                chapter.completed_tasks_count = 0

        # Определяем доступность глав
        for i, chapter in enumerate(chapters):
            if i == 0:
                chapter.is_accessible = True  # Первая глава всегда доступна
            else:
                prev_chapter = chapters[i - 1]
                prev_test = Test.objects.filter(chapter=prev_chapter).first()

                if prev_test and subscription:
                    prev_completed_count = ChapterProgress.objects.filter(
                        subscription=subscription, chapter=prev_chapter, is_completed=True
                    ).count()
                    chapter.is_accessible = prev_completed_count > 0
                else:
                    chapter.is_accessible = False

        context['course'] = course
        context['chapters'] = chapters
        return self.render_to_response(context)


class ChapterTemplateView(LoginRequiredMixin, TitleMixin, TemplateView):
    template_name = "courses/students/chapter.html"
    title = "Глава"

    def get(self, request, *args, **kwargs):
        context = super(ChapterTemplateView, self).get_context_data(*args, **kwargs)
        course_id = kwargs["course_id"]
        chapter_id = kwargs["chapter_id"]
        chapter = Chapter.objects.get(id=chapter_id)

        subscription = Subscription.objects.get(user=request.user, course_id=course_id)

        # Начинаем прогресс по главе (если его нет)
        if not ChapterProgress.objects.filter(chapter=chapter, subscription=subscription).exists():
            chapter_progress = ChapterProgress(chapter=chapter, subscription=subscription)
            chapter_progress.save()

        try:
            content = Content.objects.get(chapter_id=chapter_id)
            if content.text:
                context['text'] = content.text

            if content.video:
                context['video'] = content.video

            if content.files:
                context['file'] = content.files

        except Content.DoesNotExist:
            pass

        test = Test.objects.filter(chapter_id=chapter_id)
        tasks = Task.objects.filter(tests__in=test)

        context['course_id'] = kwargs["course_id"]
        context['chapter'] = chapter
        context['tasks'] = tasks
        return self.render_to_response(context)


class TaskTemplateView(LoginRequiredMixin, TitleMixin, TemplateView):
    template_name = "courses/students/task.html"
    title = "Задание"
    form_class = TaskAnswerForm


    def get(self, request, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        course_id, chapter_id, task_id = kwargs["course_id"], kwargs["chapter_id"], kwargs["task_id"]
        user = request.user

        # Получение прогресса по главе
        chapter_progress = ChapterProgress.objects.filter(
            subscription__user=user, subscription__course=course_id, chapter=chapter_id
        ).first()

        # Получение прогресса по выполненным заданиям
        task_progress = TaskProgress.objects.filter(chapter_progress=chapter_progress)

        # Получение текущего задания
        current_task = Task.objects.get(id=task_id)

        tasks_in_chapter = Task.objects.filter(tests__chapter_id=chapter_id)
        for task in tasks_in_chapter:
            task.is_completed = task_progress.filter(test_task__task=task).exists()


        # Получение вариантов ответа
        answers = Answer.objects.filter(task=current_task)
        correct_answers = answers.filter(is_correct=True)

        # Проверка, выполнено ли задание
        is_task_completed = task_progress.filter(test_task__task=current_task).exists()
        if is_task_completed:

            # Если задание выполнено, заполняем форму ответами
            if current_task.is_multiple_choice:
                selected_answers = [str(answer.id) for answer in correct_answers]
                context["form"] = TaskAnswerForm(task=current_task, answers=answers,
                                                 initial={"answers": selected_answers})


            elif current_task.is_compiler:
                context["form"] = None

            else:
                context["form"] = TaskAnswerForm(task=current_task,
                                                 answers=answers,
                                                 initial={"answers": correct_answers.first().text})

            # Делаем поля формы недоступными для редактирования
            for field in context["form"].fields.values():
                field.widget.attrs["readonly"] = True
                field.widget.attrs["disabled"] = True

        else:
            # Если задание не выполнено, создаем пустую форму
            context["form"] = TaskAnswerForm(task=current_task, answers=answers)

        context.update({
            "current_task": current_task,
            "is_task_completed": is_task_completed,
            "tasks_in_chapter": tasks_in_chapter,
            "answers": answers,
            "course_id": course_id,
            "chapter_id": chapter_id,
            "task_id": task_id,
        })

        return self.render_to_response(context)


    def post(self, request, **kwargs):
        task = Task.objects.get(id=kwargs["task_id"])
        answers = Answer.objects.filter(task=task)
        form = self.form_class(task, answers, data=request.POST)

        if form.is_valid():
            answers = Answer.objects.filter(task=task, is_correct=True)
            form_answers = form.cleaned_data["answers"]

            user_answer = form_answers if type(form_answers) == list else [form_answers]
            correct_answer = [str(a.id) for a in answers] if task.is_multiple_choice else [a.text for a in answers]

            if user_answer == correct_answer:

                # Получаем прогресс главы
                chapter_progress, _ = ChapterProgress.objects.get_or_create(
                    subscription__user=request.user,
                    subscription__course_id=kwargs["course_id"],
                    chapter_id=kwargs["chapter_id"]
                )

                # Добавляем выполненное задание в TestProgress
                task_progress = TaskProgress(
                    chapter_progress=chapter_progress,
                    test_task=TestTask.objects.get(task=task,
                                                   test=Test.objects.get(chapter_id=kwargs["chapter_id"])))

                task_progress.save()
                messages.success(request, "Правильный ответ!")

            else:
                messages.error(request, 'Неправильный ответ')

            return redirect("courses:task", kwargs["course_id"], kwargs["chapter_id"], kwargs["task_id"])


#                              Курсы

# Просмотр курсов
class CoursesListView(LoginRequiredMixin, TitleMixin, ListView):
    template_name = "courses/teachers/courses/courses_list.html"
    title = "Просмотр курсов"
    model = Course
    context_object_name = 'courses'

    def get_context_data(self,*args, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context


# Создание курсов
class CourseCreateView(LoginRequiredMixin, TitleMixin, SuccessMessageMixin, FormView):
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
class CourseUpdateView(LoginRequiredMixin, TitleMixin, SuccessMessageMixin, UpdateView):
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
class CourseDeleteView(LoginRequiredMixin, TitleMixin, SuccessMessageMixin, DeleteView):
    title = "Удаление курса"
    template_name = "courses/teachers/courses/course_confirm_delete.html"
    model = Course
    success_url = reverse_lazy('courses:courses_list')
    success_message = "Курс успешно удален"


#                               Категории

# Создание категорий
class CategoryCreateView(LoginRequiredMixin, TitleMixin, SuccessMessageMixin, CreateView):
    title = "Создание категории"
    template_name = "courses/teachers/courses/create_category.html"
    form_class = CreateCategoryForm
    model = Category
    success_url = reverse_lazy('courses:courses_list')
    success_message = "Категория успешно создана"


# Удалить категорию
class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    success_url = reverse_lazy('courses:courses_list')

    def get(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)


#                              Главы

# Создание глав
class ChapterUpdateView(LoginRequiredMixin, TitleMixin, SuccessMessageMixin, TemplateView):
    title = 'Редактирование главы'
    template_name = 'courses/teachers/courses/update_chapter.html'


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


#                                   Задания

# Просмотр заданий
class TaskListView(LoginRequiredMixin, TitleMixin, ListView):
    title = "Просмотр заданий"
    template_name = "courses/teachers/tasks/tasks_list.html"
    model = Task
    context_object_name = 'tasks'

    def get_queryset(self):
        return Task.objects.prefetch_related("answer_set")


# Создание задания
class TaskCreateView(LoginRequiredMixin, TitleMixin, SuccessMessageMixin, CreateView):
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

            if len(answers) == 1:
                self.object.is_text_input = True
                self.object.save()
            else:
                self.object.is_multiple_choice = True
                self.object.save()

            # Проходим по всем ответам и сохраняем их
            for answer in answers:
                answer.task = self.object  # Привязываем ответ к вопросу
                answer.save()

        return super().form_valid(form)


# Редактирование задания
class TaskUpdateView(LoginRequiredMixin, TitleMixin, SuccessMessageMixin, UpdateView):
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
class TaskDeleteView(LoginRequiredMixin, DeleteView):
    model = Task
    success_url = reverse_lazy('courses:tasks_list')

    def get(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)



#                                Тесты

# Просмотр тестов
class TestListView(LoginRequiredMixin,TitleMixin, ListView):
    title = 'Просмотр тестов'
    template_name = 'courses/teachers/tests/tests_list.html'
    model = Chapter
    context_object_name = 'courses'

    def get_queryset(self):
        # Предзагрузка задач в тестах
        tasks_prefetch = Prefetch(
            "tasks",
            queryset=Task.objects.all(),
            to_attr="prefetched_tasks"
        )

        # Предзагрузка тестов и их заданий
        tests_prefetch = Prefetch(
            "test",
            queryset=Test.objects.prefetch_related(tasks_prefetch),
            to_attr="prefetched_test"
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
class TestCreateView(LoginRequiredMixin, TitleMixin, SuccessMessageMixin, CreateView):
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
class TestDeleteView(LoginRequiredMixin, DeleteView):
    model = Test
    success_url = reverse_lazy('courses:tests_list')

    def get(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)


#                                 Студенты

# Просмотр студентов + функционал создания Excel
class StudentListView(LoginRequiredMixin, TitleMixin, ListView):
    title = 'Список студентов'
    template_name = 'courses/teachers/students/students_list.html'
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
        form = GroupSearchForm(self.request.GET or None)
        context['form'] = form
        return context


    def post(self, request, *args, **kwargs):
        form = GroupSearchForm(request.POST)
        if form.is_valid():
            group_number = form.cleaned_data['group_number']
            year = form.cleaned_data['year']
            return generate_excel(group_number, year)
        return self.get(request, *args, **kwargs)



# Создание студентов
class StudentCreateView(LoginRequiredMixin, TitleMixin, SuccessMessageMixin, CreateView):
    title = 'Создание студента'
    template_name = 'courses/teachers/students/create_student.html'
    model = User
    form_class = CreateStudentForm
    success_url = reverse_lazy('courses:students_list')
    success_message = 'Студент успешно создан'


# Удаление студента
class StudentDeleteView(LoginRequiredMixin, TitleMixin, SuccessMessageMixin, DeleteView):
    title = 'Удалить студента'
    template_name = "courses/teachers/students/student_confirm_delete.html"
    model = User
    success_url = reverse_lazy('courses:students_list')
    success_message = 'Студент успешно удален'



#                         Подписки
# Просмотр подписок, их создание
class SubscriptionListView(LoginRequiredMixin, TitleMixin, SuccessMessageMixin, ListView):
    title = "Подписки на курс"
    template_name = "courses/teachers/subscriptions/subscription_list.html"
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

        context['subscriptions'] = {course: list(groups) for course, groups in course_groups.items()}

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
            return redirect('courses:subscriptions_list')



class SubscriptionDeleteView(LoginRequiredMixin, TitleMixin, SuccessMessageMixin, View):
    title = 'Удалить подписку группы на курс'
    model = Subscription
    success_url = reverse_lazy('courses:subscription_delete')
    success_message = 'Подписка группы на курс удалена'

    @staticmethod
    def get(request, course_id, group_id):
        users_in_group = User.objects.filter(groups__id=group_id)
        Subscription.objects.filter(course_id=course_id, user__in=users_in_group).delete()
        return redirect('courses:subscriptions_list')
