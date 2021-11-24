from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model


class Registration(UserCreationForm):

    class Meta:
        fields = ('username', 'password1', 'password2')
        model = get_user_model()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Name'

    def clean_name(self):
        name = self.cleaned_data['username']
        if User.objects.filter(username=name).exists():
            raise ValidationError("User already exists")
        return name