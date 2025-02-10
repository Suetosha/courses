from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django import forms

from courses_apps.users.models import User


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label='Логин', widget=forms.TextInput(attrs={
        'class': "form-control", 'placeholder': "Введите логин пользователя"}))

    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={
        'class': "form-control", 'placeholder': "Введите пароль"}))


    class Meta:
        model = User
        fields = ('username', 'password')


class UserRegistrationForm(UserCreationForm):

    username = forms.CharField(label="Имя пользователя", widget=forms.TextInput(attrs={
        'class': "form-control", 'placeholder': "Введите имя пользователя"
    }))

    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={
        'class': "form-control", 'placeholder': "Введите пароль"}))

    password2 = forms.CharField(label='Повторите пароль', widget=forms.PasswordInput(attrs={
        'class': "form-control", 'placeholder': "Повторите пароль"}))


    first_name = forms.CharField(label='Имя', widget=forms.TextInput(attrs={
        'class': "form-control", 'placeholder': "Введите имя"}))

    last_name = forms.CharField(label='Фамилия', widget=forms.TextInput(attrs={
        'class': "form-control", 'placeholder': "Введите фамилию"}))

    group_number = forms.CharField(label='Номер группы', required=False, widget=forms.TextInput(attrs={
        'class': "form-control", 'placeholder': "Введите номер группы"
    }))

    role = forms.ChoiceField(label='', choices=(('student', 'Студент'), ('teacher', 'Преподаватель')),
                                 widget=forms.Select(attrs={'class': "btn btn-secondary dropdown-toggle"}))


    class Meta:
        model = User
        fields = ('username', 'password1', 'password2', 'first_name', 'last_name', 'group_number', 'role',)


