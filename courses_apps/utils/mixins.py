class TitleMixin:
    title = None

    def get_context_data(self,*args, **kwargs):
        context = super(TitleMixin, self).get_context_data(*args, **kwargs)
        context['title'] = self.title
        return context
