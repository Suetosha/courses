from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse, reverse_lazy

from django.views.generic import TemplateView, ListView, FormView, UpdateView, DeleteView, CreateView

from courses_apps.courses.forms import AnswerForm, CreateCourseForm, CreateCategoryForm, ChapterFormSet, \
    CreateContentForm, ChapterForm

from courses_apps.courses.models import Course, Category, Chapter, Content, Test, Subscription
from courses_apps.utils.mixins import TitleMixin, GroupRequiredMixin


class HomeTemplateView(TitleMixin, TemplateView):
    template_name = "courses/home.html"
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


class CourseTemplateView(TitleMixin, GroupRequiredMixin, TemplateView):
    template_name = "courses/course.html"
    title = "Страница курса"

    def get(self, request, *args, **kwargs):
        context = super(CourseTemplateView, self).get_context_data(*args, **kwargs)

        chapters = list(Chapter.objects.filter(course_id=kwargs["pk"]).order_by("id"))
        course = Course.objects.get(pk=kwargs["pk"])

        # Оформляем подписку юзера на данный курс
        if not Subscription.objects.filter(user=request.user, course=course).exists():
            Subscription.objects.create(user=request.user, course=course)

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
    template_name = "courses/chapter.html"
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
        context['tests'] = tests
        return self.render_to_response(context)




class TestTemplateView(TitleMixin, TemplateView):
    template_name = "courses/test.html"
    title = "Тест"
    form_class = AnswerForm


    def get(self, request, *args, **kwargs):
        context = super(TestTemplateView, self).get_context_data(*args, **kwargs)
        user = request.user

        test = Test.objects.get(id=kwargs["pk"])
        tests = Test.objects.filter(chapter_id=test.chapter_id)

        context['tests'] = tests
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



#                      Просмотр курсов

class CoursesListView(TitleMixin, ListView):
    template_name = "courses/courses_list.html"
    title = "Просмотр курсов"
    model = Course
    context_object_name = 'courses'

#                     Cоздание курсов

class CourseCreateView(TitleMixin, FormView):
    title = "Создание курса"
    template_name = "courses/create_course.html"
    form_class = CreateCourseForm
    model = Course
    success_url = reverse_lazy("courses:courses_list")

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



class CourseEditView(TitleMixin, UpdateView):
    title = "Редактирование курса"
    template_name = "courses/edit_course.html"
    model = Course
    form_class = CreateCourseForm
    success_url = reverse_lazy("courses:courses_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        course_id = self.kwargs["pk"]
        course = Course.objects.get(id=course_id)
        chapters = Chapter.objects.filter(course=course)

        form = CreateCourseForm(instance=course)

        context['form'] = form
        context['chapters'] = chapters
        return context




class CourseDeleteView(DeleteView):
    model = Course
    template_name = "courses/course_confirm_delete.html"
    success_url = reverse_lazy('courses:courses_list')





class  CategoryCreateView(TitleMixin, FormView):
    title = "Создание категории"
    template_name = "courses/create_category.html"
    form_class = CreateCategoryForm
    model = Category


    def form_valid(self, form):
        form.save()
        return redirect('courses:courses_list')



class ChapterEditView(TemplateView):
    template_name = 'courses/edit_chapter.html'

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

        # Проверяем, что форма для главы валидна
        if 'update_chapter' in request.POST.dict() and chapter_form.is_valid():
            chapter_form.save()

            return redirect(reverse_lazy('courses:edit_course', kwargs={'pk': chapter.course.id}))

        # Проверяем, что форма для контента валидна
        if 'update_content' in request.POST.dict() and content_form.is_valid():
            # Сохраняем/обновляем новый контент
            content, created = Content.objects.get_or_create(chapter=chapter)

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


            return redirect(reverse_lazy('courses:edit_chapter', kwargs={'pk': chapter.id}))

        # # Если хотя бы одна форма не валидна, возвращаем данные и ошибки
        context = self.get_context_data()
        context['form'] = chapter_form
        context['content_form'] = content_form

        return self.render_to_response(context)




