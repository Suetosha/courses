from django.contrib.auth.forms import AuthenticationForm
from django import forms
from django.core.exceptions import ValidationError

from courses_apps.courses.models import Course
from courses_apps.tests.models import ControlTest
from courses_apps.users.models import User, Group
from courses_apps.utils.generate_username import generate_username
from courses_apps.utils.generate_password import generate_password


# Форма авторизации пользователя
class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label='Логин', widget=forms.TextInput(attrs={
        'class': "form-control", 'placeholder': "Введите логин пользователя"}))

    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={
        'class': "form-control", 'placeholder': "Введите пароль"}))

    class Meta:
        model = User
        fields = ('username', 'password')


# Форма для изменения пароля в профиле пользователя, остальные поля доступны только для чтения
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'password1', 'password2', 'group_number', 'year']

    first_name = forms.CharField(label="Имя", required=False, widget=forms.TextInput(attrs={
        'class': "form-control py-4", 'placeholder': "Введите имя", 'readonly': 'readonly'}))

    last_name = forms.CharField(label="Фамилия", required=False, widget=forms.TextInput(attrs={
        'class': "form-control py-4", 'placeholder': "Введите фамилию", 'readonly': 'readonly'}))

    password1 = forms.CharField(label='Пароль', required=False, widget=forms.PasswordInput(attrs={
        'class': "form-control py-4", 'placeholder': "Введите пароль"}))

    password2 = forms.CharField(label='Повторите пароль', required=False, widget=forms.PasswordInput(attrs={
        'class': "form-control py-4", 'placeholder': "Повторите пароль"}))

    group_number = forms.CharField(label='Номер группы', required=False, widget=forms.TextInput(attrs={
        'class': "form-control py-4", 'readonly': 'readonly'
    }))

    year = forms.CharField(label='Год', required=False, widget=forms.TextInput(attrs={
        'class': "form-control", 'readonly': 'readonly'
    }))

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        if user:
            self.user = user
            self.fields["first_name"].initial = user.first_name
            self.fields["last_name"].initial = user.last_name

            group = user.groups.first()
            if group:
                self.fields["group_number"].initial = getattr(group, "number", "")
                self.fields["year"].initial = getattr(group, "year", "")

            if user.role == "teacher" or user.is_superuser:
                self.fields.pop("group_number", None)
                self.fields.pop("year", None)

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Пароли не совпадают")

        return cleaned_data

    def save(self, commit=True):
        user = self.user
        password1 = self.cleaned_data.get("password1")

        if password1:
            user.set_password(password1)

        if user.role == 'student':
            group_number = self.cleaned_data.get("group_number")
            year = self.cleaned_data.get("year")

            if group_number and year:
                group, _ = Group.objects.get_or_create(number=group_number, year=year)
                user.groups.set([group])

        if commit:
            user.save()
        return user


# Форма создания подписки
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
        self.fields['course'].queryset = Course.objects.all().order_by('title')
        self.fields['group'].queryset = Group.objects.all().order_by('number')


# Форма создания подписки на контрольный тест
class SubscriptionControlTestForm(forms.Form):
    control_test = forms.ModelChoiceField(
        label="Тест",
        queryset=None,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control', 'placeholder': 'Выберите тест'}
                            ))
    group = forms.ModelChoiceField(
        label="Группа",
        queryset=None,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control', 'placeholder': 'Выберите группу'}
                            ))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['control_test'].queryset = ControlTest.objects.all().order_by('title')
        self.fields['group'].queryset = Group.objects.all().order_by('number')


# Форма для получения экселя группы
class GroupSearchForm(forms.Form):
    groups = forms.ModelChoiceField(
        label='Номер группы и год',
        queryset=Group.objects.all().distinct().order_by('number', 'year'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


# Форма для добавления студентов путем загрузки экселя
class ImportStudentsForm(forms.Form):
    excel_file = forms.FileField(label='Загрузите Excel файл с данными студентов', required=True)


# Форма создания студента
class CreateStudentForm(forms.ModelForm):
    username = forms.CharField(
        label="Имя пользователя",
        widget=forms.TextInput(attrs={'class': "form-control", 'readonly': 'readonly'})
    )

    password = forms.CharField(
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
        fields = ['username', 'password', 'first_name', 'last_name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Генерация логина
        self.fields['username'].initial = generate_username()

        # Генерация пароля
        self.fields['password'].initial = generate_password()

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'student'

        user.username = self.cleaned_data['username']
        password = self.cleaned_data['password']

        user.set_password(password)
        user.set_password(password)

        if commit:
            user.save()

        group_number = self.cleaned_data.get('group_number')
        year = self.cleaned_data.get('year')

        group, _ = Group.objects.get_or_create(number=group_number, year=year)

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

        if commit:
            user.save()

        return user
