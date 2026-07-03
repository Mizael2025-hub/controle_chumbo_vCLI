from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserChangeForm,
    UserCreationForm,
)

from .models import User


class LoginForm(AuthenticationForm):
    username = forms.EmailField(label="E-mail", widget=forms.EmailInput(attrs={"autocomplete": "email"}))

    field_order = ["username", "password"]


class ProfileForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ["name"]


class UserCreationForm(UserCreationForm):
    username = None

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email", "name", "role")


class UserChangeForm(UserChangeForm):
    username = None

    class Meta(UserChangeForm.Meta):
        model = User
        fields = ("email", "name", "role")
