from dal import autocomplete
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple

from goosetools.industry.models import OrderLimitGroup, Ship, ShipOrder
from goosetools.users.models import Character


class ShipOrderForm(forms.Form):
    recipient_character = forms.ModelChoiceField(
        label="Recipient Character",
        queryset=Character.objects.all(),
        initial=0,
    )
    ship = forms.ModelChoiceField(
        queryset=Ship.objects.all(),
        initial="Vexor Navy Issue",
        widget=autocomplete.ModelSelect2(url="industry:ship-autocomplete"),
        required=False,
    )
    payment_method = forms.ChoiceField(choices=ShipOrder.PAYMENT_METHODS)
    notes = forms.CharField(initial="", required=False)
    quantity = forms.IntegerField(min_value=1, initial=1)


class OrderLimitGroupForm(forms.ModelForm):
    class Meta:
        model = OrderLimitGroup
        fields = ["name", "days_between_orders"]

    ships = forms.ModelMultipleChoiceField(
        queryset=Ship.objects.filter(free=True).all(),
        widget=FilteredSelectMultiple("verbose name", is_stacked=False),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields["ships"].initial = self.instance.ship_set.all()

    # pylint: disable=unused-argument,signature-differs
    def save(self, *args, **kwargs):
        instance = super().save(commit=False)
        self.fields["ships"].initial.update(order_limit_group=None)
        self.cleaned_data["ships"].update(order_limit_group=instance)
        return instance
