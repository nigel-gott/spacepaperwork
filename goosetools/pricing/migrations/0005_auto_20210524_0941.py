# Generated by Django 3.1.4 on 2021-05-24 09:41

from django.db import migrations, models
import django.db.models.deletion

def reset_order_to_level(self):
    self.order = self.calc_level()

def calc_level(self):
    if self.user is not None:
        if self.corp is None and self.permission is None:
            # Just user
            level = 10
        elif self.corp is None:
            # Permission and User
            level = 12
        elif self.permission is None:
            # Corp and User
            level = 15
        else:
            # Corp and User and Permission
            level = 20
    elif self.corp is not None:
        # User is none
        if self.permission is None:
            # Just corp
            level = 5
        else:
            # Corp and Permission
            level = 7
    elif self.permission is not None:
        # Just permission
        level = 3
    else:
        # No matcher set, matches everyone.
        level = 0

    if not self.allow_or_deny:
        # A deny of the same level must override it.
        level = level + 1

    return level
from goosetools.users.models import SHIP_PRICE_ADMIN

# pylint: disable=unused-argument
def reverse(apps, schema_editor):
    pass

# pylint: disable=unused-argument
def combine_names(apps, schema_editor):
    ItemMarketDataEvent = apps.get_model("pricing", "ItemMarketDataEvent")
    CrudAccessController = apps.get_model("users", "CrudAccessController")
    PermissibleEntity = apps.get_model("users", "PermissibleEntity")
    PermissibleEntity.reset_order_to_level = reset_order_to_level
    PermissibleEntity.calc_level = calc_level
    GoosePermission = apps.get_model("users", "GoosePermission")
    PriceList = apps.get_model("pricing", "PriceList")

    access_controller = CrudAccessController.objects.create()
    eem_pl = PriceList.objects.create(
        owner=None,
        name="eve-echoes-market.com live prices",
        access_controller=access_controller,
        api_type="eve_echoes_market",
        default=True,
    )
    ItemMarketDataEvent.objects.update(price_list=eem_pl)
    everyone = PermissibleEntity(
        permission=None,
        corp=None,
        user=None,
        allow_or_deny=True,
        built_in=False,
    )
    everyone.reset_order_to_level()
    everyone.save()
    access_controller.viewable_by.add(everyone)
    access_controller.usable_by.add(everyone)
    ship_price_admin, _ = GoosePermission.objects.get_or_create(name=SHIP_PRICE_ADMIN)
    ship_price_admins = PermissibleEntity(
        permission=ship_price_admin,
        corp=None,
        user=None,
        allow_or_deny=True,
        built_in=True,
    )
    ship_price_admins.reset_order_to_level()
    ship_price_admins.save()
    access_controller.adminable_by.add(ship_price_admins)

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0016_auto_20210508_1403'),
        ('pricing', '0004_auto_20210503_1932'),
    ]

    operations = [
        migrations.CreateModel(
            name='PriceList',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField(unique=True)),
                ('description', models.TextField()),
                ('tags', models.TextField()),
                ('api_type', models.TextField(choices=[('eve_echoes_market', 'eve_echoes_market'), ('google_sheet', 'google_sheet'), ('manual', 'manual')])),
                ('google_sheet_id', models.TextField(blank=True, null=True)),
                ('google_sheet_cell_range', models.TextField(blank=True, null=True)),
                ('default', models.BooleanField(default=True)),
            ],
        ),
        migrations.RemoveIndex(
            model_name='itemmarketdataevent',
            name='pricing_ite_time_4dca4a_idx',
        ),
        migrations.AddField(
            model_name='itemmarketdataevent',
            name='manual_override_price',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='itemmarketdataevent',
            name='price_list',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='pricing.pricelist'),
        ),
        migrations.AddIndex(
            model_name='itemmarketdataevent',
            index=models.Index(fields=['price_list', '-time'], name='pricing_ite_price_l_dec037_idx'),
        ),
        migrations.AddField(
            model_name='pricelist',
            name='access_controller',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='users.crudaccesscontroller'),
        ),
        migrations.AddField(
            model_name='pricelist',
            name='owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='users.gooseuser'),
        ),
        migrations.RunPython(combine_names, reverse),
    ]
