from django import forms

class ValidateGamePasswordForm(forms.Form):
    password = forms.CharField(max_length=10)