from django.contrib import messages
from django.core.signals import request_started
from django.shortcuts import redirect
from django.views.generic import TemplateView

from courses_apps.courses.forms import AnswerForm
from courses_apps.courses.models import Course, Category, Chapter, Content, Test
from courses_apps.utils.mixins import TitleMixin


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


class CourseTemplateView(TitleMixin, TemplateView):
    template_name = "courses/course.html"
    title = "Страница курса"

    def get(self, request, *args, **kwargs):
        context = super(CourseTemplateView, self).get_context_data(*args, **kwargs)

        chapters = list(Chapter.objects.filter(course_id=kwargs["pk"]).order_by("id"))

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
        except Content.DoesNotExist:
            pass

        tests = Test.objects.filter(chapter_id=kwargs["pk"])

        if context.get("text"):
            context['text'] = content.text

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







