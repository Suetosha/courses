
from django.views.generic import TemplateView

from courses_apps.courses.models import Course
from courses_apps.utils.mixins import TitleMixin


class HomeTemplateView(TitleMixin, TemplateView):
    template_name = "courses/home.html"
    title = "Курсы"

    def get(self, request, *args, **kwargs):
        context = super(HomeTemplateView, self).get_context_data(*args, **kwargs)
        courses = Course.objects.filter(status='published')
        context['courses'] = courses
        return self.render_to_response(context)





