from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Account, JobSeeker


class LoginForm(forms.ModelForm):
    """Form used to log a user in."""

    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )

    class Meta:
        model = Account
        fields = ["email", "password"]


class SignupForm(UserCreationForm):
    """Form used to register the user."""

    class Meta:
        model = Account
        fields = [
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
            "account_type",
        ]


class UserUpdateForm(forms.ModelForm):
    """Form used to update user information."""

    class Meta:
        model = Account
        fields = ["first_name", "last_name"]


class JSProfileUpdateForm(forms.ModelForm):
    """Form used to update job seeker profile."""

    class Meta:
        model = JobSeeker
        fields = ["resume"]
