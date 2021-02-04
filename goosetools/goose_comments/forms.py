from django import forms
from django.utils.translation import gettext_lazy as _
from django_comments.forms import CommentForm


class CommentFormWithoutEmailUrl(CommentForm):
    email = forms.EmailField(label=_("Email address"), required=False)
