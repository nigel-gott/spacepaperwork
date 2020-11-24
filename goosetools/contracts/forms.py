from dal import autocomplete
from django import forms

from goosetools.items.models import System
from goosetools.users.models import Character


class ItemMoveAllForm(forms.Form):
    character = forms.ModelChoiceField(
        label="Character To Contract Items To",
        queryset=Character.objects.all(),
        initial=0,
        widget=autocomplete.ModelSelect2(url="character-autocomplete"),
        help_text="This Person Will Recieve The Items If They Approve The Contract",
    )
    system = forms.ModelChoiceField(
        queryset=System.objects.all(),
        initial=0,
        widget=autocomplete.ModelSelect2(url="system-autocomplete"),
        help_text="The System Where You Made The Real In-Game Contract",
    )
