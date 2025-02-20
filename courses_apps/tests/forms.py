from django import forms

from courses_apps.courses.models import Chapter
from courses_apps.tests.models import *
from django.forms import inlineformset_factory


class CreateTaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["question", "is_compiler"]

    question = forms.CharField(
        label='Вопрос:',
        widget=forms.Textarea(attrs={
            'class': "form-control",
            'placeholder': "Введите текст вопроса",
            'required': 'Введите текст вопроса'
        }))

    is_compiler = forms.BooleanField(
        label='Добавить компилятор к заданию',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )




class AnswerTestForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['text', 'is_correct']

    text = forms.CharField(
        label='Текст ответа',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите текст ответа',
            'required': 'required',
        })
    )

    is_correct = forms.BooleanField(
        label='Верный ответ',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input form-check-inline'
        })
    )



# Создаём InlineFormSet для модели Answer - create_task/update_task (Для динамического добавления вопросов)
AnswerFormCreateSet = inlineformset_factory(
    Task, Answer,
    form=AnswerTestForm,
    fields=['text', 'is_correct'],
    extra=1,
    can_delete=True
)

# Создаём InlineFormSet для модели Answer - update_task
AnswerFormUpdateSet = inlineformset_factory(
    Task, Answer,
    form=AnswerTestForm,
    fields=['text', 'is_correct'],
    extra=0,
)


class CreateTestForm(forms.ModelForm):
    class Meta:
        model = Test
        fields = ["chapter", "tasks"]


    chapter = forms.ModelChoiceField(
        queryset=Chapter.objects.all(),
        required=True,
        empty_label="Выберите главу",
        label="Глава"
    )

    tasks = forms.ModelMultipleChoiceField(
        queryset=Task.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Задания"
    )