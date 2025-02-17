from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.contrib import messages

from courses_apps.courses.models import Course, Subscription
from courses_apps.users.models import Group


class TitleMixin:
    title = None

    def get_context_data(self,*args, **kwargs):
        context = super(TitleMixin, self).get_context_data(*args, **kwargs)
        context['title'] = self.title
        return context



# Миксин для проверки наличия подписки на данный курс
class SubscriptionRequiredMixin(LoginRequiredMixin):

    course_model = None

    def dispatch(self, request, *args, **kwargs):

        course_id = kwargs.get("course_id")
        course = Course.objects.filter(id=course_id).first()
        is_sub_exist = Subscription.objects.filter(course=course).exists()

        # Если курс не найден или нет подписки — редирект на список курсов
        if not course or not Subscription.objects.filter(course=course).exists():
            messages.error(request, "У вас нет доступа к этому курсу")
            return redirect("courses:home")

        return super().dispatch(request, *args, **kwargs)
