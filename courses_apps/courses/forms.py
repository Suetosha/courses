from django import forms
from django.forms import inlineformset_factory

from courses_apps.courses.models import Course, Category, Chapter, Content



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
            self.fields["answers"] = forms.CharField(
                label='Введите код:',
                widget=forms.Textarea(attrs={
                    'class': 'form-control custom-textarea',
                    'placeholder': 'Введите код',
                    'required': 'Введите код',
                    'rows': 10,
                    'cols': 50
                })
            )


        elif task.is_multiple_choice:

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







