from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm
from django import forms
from django.template.context_processors import request

from courses_apps.users.models import User, Group


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

    group_number = forms.CharField(label='Номер группы', widget=forms.TextInput(attrs={
        'class': "form-control", 'placeholder': "Введите номер группы"
    }))

    year = forms.CharField(label='Год', widget=forms.TextInput(attrs={
        'class': "form-control", 'placeholder': "Введите год"
    }))

    role = forms.ChoiceField(label='', choices=(('student', 'Студент'), ('teacher', 'Преподаватель')),
                                 widget=forms.Select(attrs={'class': "btn btn-secondary dropdown-toggle"}))

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2', 'first_name', 'last_name', 'group_number', 'year', 'role',)


    def save(self, commit=True):
        user = super().save(commit=False)

        if commit:
            user.save()

            group_number = self.cleaned_data.get('group_number')
            year = self.cleaned_data.get('year')

            if group_number or year:
                group, _ = Group.objects.get_or_create(number=group_number, year=year)
                user.groups.add(group)
                user.save()

        return user



class UserProfileForm(UserChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print(kwargs)
        user = kwargs.pop('instance', None)
        group = user.groups.first()
        if group:
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