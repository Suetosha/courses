from django.contrib.auth.forms import AuthenticationForm, UserChangeForm
from django import forms

from courses_apps.courses.models import Course
from courses_apps.users.models import User, Group
from courses_apps.utils.generate_username import generate_username
from courses_apps.utils.generate_password import generate_password


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label='Логин', widget=forms.TextInput(attrs={
        'class': "form-control", 'placeholder': "Введите логин пользователя"}))

    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={
        'class': "form-control", 'placeholder': "Введите пароль"}))


    class Meta:
        model = User
        fields = ('username', 'password')



class UserProfileForm(UserChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = kwargs.pop('instance', None)
        group = user.groups.first()

        if user and user.role == "teacher" or (user and user.is_superuser):
            # Убираем поля для учителей и суперпользователей
            self.fields.pop("group_number", None)
            self.fields.pop("year", None)
        else:
            self.fields["group_number"].initial = group.number
            self.fields["year"].initial = group.year

        for field in self.fields.values():
            field.help_text = ''
        if "password" in self.fields:
            del self.fields["password"]


    first_name = forms.CharField(label="Имя", required=False, widget=forms.TextInput(attrs={
        'class': "form-control py-4", 'placeholder': "Введите имя", 'readonly': 'readonly'}))

    last_name = forms.CharField(label="Фамилия", required=False, widget=forms.TextInput(attrs={
        'class': "form-control py-4", 'placeholder': "Введите фамилию", 'readonly': 'readonly'}))

    password1 = forms.CharField(label='Пароль', required=False, widget=forms.PasswordInput(attrs={
        'class': "form-control py-4", 'placeholder': "Введите пароль"}))

    password2 = forms.CharField(label='Повторите пароль', required=False, widget=forms.PasswordInput(attrs={
        'class': "form-control py-4", 'placeholder': "Повторите пароль"}))

    group_number = forms.CharField(label='Номер группы', required=True, widget=forms.TextInput(attrs={
        'class': "form-control py-4", 'placeholder': "Введите номер группы", 'readonly': 'readonly'
    }))

    year = forms.CharField(label='Год', required=True, widget=forms.TextInput(attrs={
        'class': "form-control", 'placeholder': "Введите год", 'readonly': 'readonly'
    }))


    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'password1', 'password2', 'group_number', 'year']

    def save(self, commit=True):
        user = super().save(commit=False)

        group_number = self.cleaned_data.get('group_number')
        year = self.cleaned_data.get('year')

        group, _ = Group.objects.update_or_create(number=group_number, year=year)
        if group:
            user.groups.set([group])

        if commit:
            user.save()

        return user


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



class ImportStudentsForm(forms.Form):
    excel_file = forms.FileField(label='Загрузите Excel файл с данными студентов', required=True)




class CreateStudentForm(forms.ModelForm):
    username = forms.CharField(
        label="Имя пользователя",
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
        self.fields['username'].initial = generate_username()

        # Генерация пароля
        self.fields['password1'].initial = generate_password()

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'student'

        # Устанавливаем логин и пароль
        user.username = self.cleaned_data['username']
        password = self.cleaned_data['password1']

        user.set_password(password)
        user.set_password(password)

        # Сохраняем пользователя, чтобы получить айди
        if commit:
            user.save()

        # Получаем номер группы и год
        group_number = self.cleaned_data.get('group_number')
        year = self.cleaned_data.get('year')

        # Создаем или находим группу
        group, _ = Group.objects.get_or_create(number=group_number, year=year)

        # Добавляем пользователя в группу после сохранения
        user.groups.add(group)

        return user


# Создание учителя
class CreateTeacherForm(forms.ModelForm):
    username = forms.CharField(
        label="Имя пользователя",
        widget=forms.TextInput(attrs={'class': "form-control", 'readonly': 'readonly'})
    )

    password1 = forms.CharField(
        label='Пароль',
        required=False,
        widget=forms.TextInput(attrs={'class': "form-control", 'readonly': 'readonly'})
    )

    first_name = forms.CharField(
        label="Имя преподавателя", required=False,
        widget=forms.TextInput(attrs={'class': "form-control py-4", 'placeholder': "Введите имя"})
    )

    last_name = forms.CharField(
        label="Фамилия преподавателя", required=False,
        widget=forms.TextInput(attrs={'class': "form-control py-4", 'placeholder': "Введите фамилию"})
    )


    class Meta:
        model = User
        fields = ['username', 'password1', 'first_name', 'last_name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Генерация логина
        self.fields['username'].initial = generate_username()

        # Генерация пароля
        self.fields['password1'].initial = generate_password()


    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'teacher'

        # Устанавливаем логин и пароль
        user.username = self.cleaned_data['username']
        password = self.cleaned_data['password1']

        user.set_password(password)
        user.set_password(password)

        # Сохраняем пользователя, чтобы получить айди
        if commit:
            user.save()

        return user


