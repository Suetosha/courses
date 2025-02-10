from django import forms


class AnswerForm(forms.Form):
    answer = forms.CharField(label='Ответ', widget=forms.TextInput(attrs={
        'class': "form-control", 'placeholder': "Введите ответ", 'required': 'Нужно ввести ответ'}))


    class Meta:
        fields = ('answer',)