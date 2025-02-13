from django import forms
from django.forms import inlineformset_factory

from courses_apps.courses.models import Course, Category, Chapter, Content


class AnswerForm(forms.Form):
    class Meta:
        fields = ('answer',)

    answer = forms.CharField(label='Ответ', widget=forms.TextInput(attrs={
        'class': "form-control", 'placeholder': "Введите ответ", 'required': 'Нужно ввести ответ'}))




class CreateCourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'status', 'category']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()


    title = forms.CharField(label='Курс', widget=forms.TextInput(attrs={
        'class': "form-control", 'placeholder': "Введите название курса", 'required': 'Введите название курса'}))

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

    title = forms.CharField(label='Глава:', widget=forms.TextInput(attrs={
        'class': "form-control", 'placeholder': "Введите название глав", 'required': 'Введите название глав'}))


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

    name = forms.CharField(label='Категория', widget=forms.TextInput(attrs={
        'class': "form-control", 'placeholder': "Введите новую категорию", 'required': 'Нужно ввести новую категорию'}))



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




