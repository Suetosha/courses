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


# Форма создания задания для контрольного теста
class CreateControlTaskForm(CreateTaskForm):
    class Meta(CreateTaskForm.Meta):
        fields = CreateTaskForm.Meta.fields + ['point']

    point = forms.ChoiceField(
        label="Баллы за задание",
        choices=[(i, str(i)) for i in range(1, 6)],
        widget=forms.Select(attrs={'class': 'form-select mt-1', 'style': 'width: 100px;'}),
        initial=1
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


class ControlTaskAnswerForm(forms.Form):
    def __init__(self, *args, task=None, answers=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.task = task

        if task:

            # Поле для текста (если `is_text_input=True`)
            if task.is_text_input:
                self.fields[task.id] = forms.CharField(
                    label="Введите текстовый ответ",
                    widget=forms.TextInput(attrs={
                        'class': 'form-control',
                        'placeholder': 'Введите ваш ответ здесь...'
                    }),
                    required=False
                )

            # Поле для кода (если `is_compiler=True`)
            elif task.is_compiler:
                self.fields[task.id] = forms.CharField(
                    label="Ваш код",
                    widget=forms.Textarea(attrs={
                        'class': 'form-control',
                        'rows': 10,
                        'placeholder': 'Напишите ваш код здесь...'
                    }),
                    required=False
                )

            # Чекбоксы (если `is_multiple_choice=True`)
            elif task.is_multiple_choice:
                self.fields[task.id] = forms.CharField(
                    label="Выберите несколько вариантов ответа",
                    widget=forms.CheckboxSelectMultiple(
                        choices=[(answer.id, answer.text) for answer in answers]
                    ),
                    required=False
                )

            # Радиокнопки (по умолчанию)
            else:
                self.fields[task.id] = forms.ChoiceField(
                    label="Выберите один вариант",
                    widget=forms.RadioSelect,
                    choices=[(answer.id, answer.text) for answer in answers],
                    required=False
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
    Task,
    Answer,
    form=AnswerTestForm,
    fields=['text', 'is_correct'],
    extra=0,
    can_delete=True
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


# Форма для изменения названия контрольного теста
class ControlTestTitleForm(forms.ModelForm):
    class Meta:
        model = ControlTest
        fields = ['title']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите новое название теста'}),
        }
        labels = {
            'title': 'Название контрольного теста',
        }
