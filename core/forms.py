from django.forms import ModelForm
from core.models import Fleet


class FleetForm(ModelForm):
    class Meta:
        model = Fleet
        fields = '__all__'
