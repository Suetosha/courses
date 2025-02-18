from django import forms
from django.forms import inlineformset_factory

import secrets
import string

from courses_apps.courses.models import Course, Category, Chapter, Content, Task, Answer, Test
from courses_apps.users.models import User, Group


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


# Создание студента
class CreateStudentForm(forms.ModelForm):
    username = forms.CharField(
        label="Логин студента",
        widget=forms.TextInput(attrs={'class': "form-control", 'readonly': 'readonly'})
    )

    password1 = forms.CharField(
        label='Пароль',
        required=False,
        widget=forms.TextInput(attrs={'class': "form-control", 'readonly': 'readonly'})
    )

    first_name = forms.CharField(
        label="Имя", required=False,
        widget=forms.TextInput(attrs={'class': "form-control py-4", 'placeholder': "Введите имя"})
    )

    last_name = forms.CharField(
        label="Фамилия", required=False,
        widget=forms.TextInput(attrs={'class': "form-control py-4", 'placeholder': "Введите фамилию"})
    )

    group_number = forms.CharField(
        label='Номер группы',
        required=True,
        widget=forms.TextInput(attrs={'class': "form-control py-4", 'placeholder': "Введите номер группы"})
    )

    year = forms.IntegerField(
        label='Год',
        required=True,
        widget=forms.NumberInput(attrs={'class': "form-control", 'placeholder': "Введите год"})
    )

    class Meta:
        model = User
        fields = ['username', 'password1', 'first_name', 'last_name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Генерация логина
        self.fields['username'].initial = self.generate_username()

        # Генерация пароля
        self.fields['password1'].initial = self.generate_password()

    def generate_username(self):
        """Генерация уникального логина"""
        return f"stu{secrets.token_hex(4)}"  # Пример: stu3f7a2b5c

    def generate_password(self, length=8):
        """Генерация случайного пароля"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'student'

        # Устанавливаем username и пароль
        user.username = self.cleaned_data['username']
        password = self.cleaned_data['password1']

        user.set_password(password)
        user.set_password(password)

        # Сохраняем пользователя, чтобы получить id
        if commit:
            user.save()

        # Получаем номер группы и год
        group_number = self.cleaned_data.get('group_number')
        year = self.cleaned_data.get('year')

        # Создаем или находим группу
        group, _ = Group.objects.get_or_create(number=group_number, year=year)

        # Добавляем пользователя в группу ПОСЛЕ сохранения
        user.groups.add(group)

        return user


class GroupSearchForm(forms.Form):
    group_number = forms.ChoiceField(
        label='Номер группы',
        choices=[],
        widget=forms.Select(attrs={'class': 'form-control', 'placeholder': 'Выберите номер группы'})
    )
    year = forms.ChoiceField(
        label='Год',
        choices=[],
        widget=forms.Select(attrs={'class': 'form-control', 'placeholder': 'Выберите год'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Получаем уникальные номера групп и года
        group_numbers = Group.objects.values_list('number', flat=True).distinct().order_by('number')
        years = Group.objects.values_list('year', flat=True).distinct().order_by('year')

        # Добавляем эти значения в поля
        self.fields['group_number'].choices = [(num, num) for num in group_numbers]
        self.fields['year'].choices = [(year, year) for year in years]


class SubscriptionForm(forms.Form):
    course = forms.ModelChoiceField(
        label="Курс",
        queryset=None,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control', 'placeholder': 'Выберите курс'}
                            ))
    group = forms.ModelChoiceField(
        label="Группа",
        queryset=None,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control', 'placeholder': 'Выберите группу'}
                            ))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        courses = Course.objects.all().order_by('title')
        groups = Group.objects.all().order_by('number')

        self.fields['course'].queryset = courses
        self.fields['group'].queryset = groups
