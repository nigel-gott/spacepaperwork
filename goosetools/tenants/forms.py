from django import forms

from goosetools.tenants.models import Client


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ("name",)
