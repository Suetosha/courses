from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages

from courses_apps.courses.models import Course, Chapter
from courses_apps.tests.models import Test
from courses_apps.users.models import Subscription, ChapterProgress


class TitleMixin:
    title = None

    def get_context_data(self, *args, **kwargs):
        context = super(TitleMixin, self).get_context_data(*args, **kwargs)
        context['title'] = self.title
        return context


# Миксин для проверки наличия подписки на данный курс
class SubscriptionRequiredMixin:

    def dispatch(self, request, *args, **kwargs):
        course_id = kwargs.get("course_id")
        course = Course.objects.filter(id=course_id).first()

        if not course or not Subscription.objects.filter(course=course).exists():
            messages.error(request, "У вас нет доступа к этому курсу")
            return redirect("courses:home")

        return super().dispatch(request, *args, **kwargs)


# Миксин для закрытия доступа к главе, если предыдущая не была выполнена
class ChapterAccessMixin:
    def dispatch(self, request, *args, **kwargs):
        chapter_id = kwargs.get("chapter_id")
        user = request.user

        try:
            chapter = Chapter.objects.get(id=chapter_id)
        except Chapter.DoesNotExist:
            raise PermissionDenied("Глава не найдена")

        previous_chapter = Chapter.objects.filter(course=chapter.course, id__lt=chapter.id).order_by("-id").first()

        if previous_chapter:
            chapter_progress = ChapterProgress.objects.filter(
                subscription__user=user, chapter=previous_chapter, is_completed=True
            ).exists()

            if not chapter_progress:
                return redirect("courses:home")

        return super().dispatch(request, *args, **kwargs)


# Миксин для закрытия доступа к тестам, наследуется от ChapterAccessMixin
class TestAccessMixin(ChapterAccessMixin):
    def dispatch(self, request, *args, **kwargs):
        test_id = kwargs.get("test_id")

        try:
            test = Test.objects.get(id=test_id)
            chapter = test.chapter
        except Test.DoesNotExist:
            raise PermissionDenied("Тест не найден")

        # Проверяем доступ к главе
        response = super().dispatch(request, *args, chapter_id=chapter.id, **kwargs)

        # Если ChapterAccessMixin возвращает директ, то прекращаем выполнять код
        if isinstance(response, redirect):
            return response

        return super().dispatch(request, *args, **kwargs)


# Миксин для закрытия доступа к функционалу студентов
class RedirectTeacherMixin:
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_superuser or request.user.role == "teacher":
            return redirect("courses:courses_list")

        return super().dispatch(request, *args, **kwargs)


# Миксин для закрытия доступа к функционалу преподавателей или суперюзеров
class RedirectStudentMixin:
    def dispatch(self, request, *args, **kwargs):
        if request.user.role == "student":
            return redirect("courses:home")
        return super().dispatch(request, *args, **kwargs)
