# -*- coding: utf-8 -*-
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.password_validation import validate_password
from accounts.models import UnoUser
from django import forms


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput())

    def clean(self):
        username = self.cleaned_data['username']
        password = self.cleaned_data['password']
        user = UnoUser.objects.filter(username=username).first()
        if not user or user and not user.check_password(password):
            raise forms.ValidationError('Username and password do not match!')
        return self.cleaned_data


class RegisterForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.fields['gender'] = forms.CharField(widget=forms.Select(
            choices=UnoUser.GENDER_CHOICES, attrs={'class': 'browser-default'}))

    class Meta(UserCreationForm.Meta):
        model = UnoUser
        fields = ('first_name', 'last_name', 'email', 'gender') + \
            UserCreationForm.Meta.fields + ('date_of_birth',)
        widgets = {
            'password': forms.PasswordInput(),
            'date_of_birth': forms.DateInput(attrs={'type': 'date'})
        }

    def clean_password2(self):
        password1 = self.cleaned_data["password1"]
        password2 = self.cleaned_data["password2"]
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Your passwords do not match!")
        return password2


class UpdateProfileForm(UserChangeForm):
    password = None
    new_password = forms.CharField(
        widget=forms.PasswordInput(), required=False)

    def __init__(self, *args, **kwargs):
        super(UpdateProfileForm, self).__init__(*args, **kwargs)
        self.fields['gender'] = forms.CharField(widget=forms.Select(
            choices=UnoUser.GENDER_CHOICES, attrs={'class': 'browser-default'}))
        self.fields['username'].widget.attrs['readonly'] = True

    class Meta(UserChangeForm.Meta):
        model = UnoUser
        fields = ('first_name', 'last_name', 'email', 'gender') + \
            UserCreationForm.Meta.fields + \
            ('date_of_birth', 'photo', 'new_password')
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'photo': forms.HiddenInput()
        }

    def clean_new_password(self):
        new_password = self.cleaned_data['new_password']
        try:
            if not new_password:
                return
            validate_password(new_password)
            return new_password
        except forms.ValidationError as e:
            raise forms.ValidationError(e)
