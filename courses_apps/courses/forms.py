from django import forms
from django.forms import inlineformset_factory

from courses_apps.courses.models import Course, Category, Chapter, Content, Task, Answer, Test


class AnswerForm(forms.Form):
    class Meta:
        fields = ('answer',)

    answer = forms.CharField(
        label='Ответ',
        widget=forms.TextInput(attrs={
            'class': "form-control",
            'placeholder': "Введите ответ",
            'required': 'Нужно ввести ответ'
        }))




class CreateCourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'status', 'category']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()


    title = forms.CharField(
        label='Курс',
        widget=forms.TextInput(attrs={
            'class': "form-control",
            'placeholder': "Введите название курса",
            'required': 'Введите название курса'
        }))


    description = forms.CharField(
        label='Описание',
        widget=forms.Textarea(attrs={
            'class': "form-control",
            'rows': 5,
            'placeholder': "Описание курса",
            'required': 'Нужно написать описание курса'
        }))


    status = forms.ChoiceField(
        choices=Course.STATUS_CHOICES,
        label='Статус',
        widget=forms.Select(attrs={'class': "form-select"})
    )


    category = forms.ModelChoiceField(
        queryset=None,
        label='Категория',
        widget=forms.Select(attrs={'class': "form-select"}))



class ChapterForm(forms.ModelForm):
    class Meta:
        model = Chapter
        fields = ['title']

    title = forms.CharField(
        label='Глава:',
        widget=forms.TextInput(attrs={
            'class': "form-control",
            'placeholder': "Введите название глав",
            'required': 'Введите название глав'
        }))


# Создаём InlineFormSet для модели Chapter (Для динамического добавления глав)
ChapterFormSet = inlineformset_factory(
    Course,
    Chapter,
    form=ChapterForm,
    extra=1,  # Изначальное количество глав
    can_delete=True  # Возможность удалить главы
)



class CreateCategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']

    name = forms.CharField(
        label='Категория',
        widget=forms.TextInput(attrs={
            'class': "form-control",
            'placeholder': "Введите новую категорию",
            'required': 'Нужно ввести новую категорию'
        }))



class CreateContentForm(forms.ModelForm):
    class Meta:
        model = Content
        fields = ['text', 'video', 'files']

    text = forms.CharField(
        label='Текст',
        widget=forms.Textarea(attrs={
            'class': "form-control",
            'placeholder': "Введите текст для главы",
            'required': 'required',
            'rows': 4
        }),

    )

    video = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'style': 'max-width: 500px;',
            'accept': 'video/mp4',



        }),

    )
    files = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'style': 'max-width: 500px;',
            'accept': '.pdf',
        }),

    )


class CreateTaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["question"]

    question = forms.CharField(
        label='Вопрос:',
        widget=forms.TextInput(attrs={
            'class': "form-control",
            'placeholder': "Введите текст вопроса",
            'required': 'Введите текст вопроса'
        }))


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
        fields = ['chapter', 'tasks']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tasks"].queryset = Task.objects.all()
        self.fields["chapter"].queryset = Chapter.objects.all()


    chapter = forms.ModelChoiceField(
        queryset=Chapter.objects.none(),
        required=True,
        empty_label="Выберите главу",
        label="Глава"
    )

    tasks = forms.ModelMultipleChoiceField(
        queryset=Task.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Задания"
    )







