from django import forms

from courses_apps.courses.models import Chapter
from courses_apps.tests.models import *
from django.forms import inlineformset_factory


# Форма для создания задания
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


# Форма для ответа
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


# Создаём InlineFormSet для модели Answer - в create_task или update_task (Для динамического добавления вопросов)
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

# Форма создания теста
class CreateTestForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CreateTestForm, self).__init__(*args, **kwargs)
        self.fields['chapter'].label_from_instance = lambda chapter: f'{chapter.title} - {chapter.course.title}'

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


# Форма для загрузки заданий через эксель форму
class ImportTasksForm(forms.Form):
    excel_file = forms.FileField()
