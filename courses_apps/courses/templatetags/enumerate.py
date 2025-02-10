from django import template

register = template.Library()

# Добавляет индекс к элементу списка
@register.filter(name='enumerate')
def enumerate_list(value):
    return enumerate(value, start=1)