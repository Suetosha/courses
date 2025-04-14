from django import forms
from django.forms import inlineformset_factory

from courses_apps.courses.models import Course, Category, Chapter, Content


# Форма для ответа в задании
# Имеет 4 варианта:
# 1) Текстовое поле
# 2) Поле для кода
# 3) Радиокнопки для одного правильного ответа
# 4) Чекбоксы для нескольких правильных ответов

class TaskAnswerForm(forms.Form):
    def __init__(self, task, answers, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if task.is_text_input:
            # Если нужно текстовое поле ввода ответа
            self.fields["answers"] = forms.CharField(
                label="Ответ",
                widget=forms.TextInput(attrs={
                    "class": "form-control",
                    "placeholder": "Введите ответ",
                    "required": "required"
                })
            )

        elif task.is_compiler:
            # Если нужно большое поле для кода
            compiler_form = CompilerForm()
            self.fields["compiler"] = compiler_form.fields["compiler"]
            self.fields["answers"] = compiler_form.fields["answer"]


        else:
            choices = [(answer.id, answer.text) for answer in answers]

            correct_count = answers.filter(is_correct=True).count()

            if correct_count == 1:
                # Радиокнопки, если один правильный ответ
                self.fields["answers"] = forms.ChoiceField(
                    choices=choices,
                    widget=forms.RadioSelect,
                    label="Выберите один ответ",
                )

            else:
                # Чекбоксы, если несколько правильных ответов
                self.fields["answers"] = forms.MultipleChoiceField(
                    choices=choices,
                    widget=forms.CheckboxSelectMultiple,
                    label="Выберите один или несколько ответов",
                )


# Форма для компилятора
class CompilerForm(forms.Form):
    compiler = forms.CharField(
        label='Введите код:',
        widget=forms.Textarea(attrs={
            'class': 'form-control custom-textarea',
            'placeholder': 'Введите код',
            'rows': 10,
            'cols': 50
        }),
        required=True,
        error_messages={'required': 'Поле не может быть пустым!'}
    )

    answer = forms.CharField(
        label='Ответ',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'readonly': True,
            'rows': 10,
            'cols': 50
        })
    )


# Форма для создания курса
class CreateCourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'status', 'category']

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
        queryset=Category.objects.all(),
        label='Категория',
        widget=forms.Select(attrs={'class': "form-select"}))


# Форма для создания глав
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


# Форма для создания категории
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


# Форма для создания контента для глав
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
