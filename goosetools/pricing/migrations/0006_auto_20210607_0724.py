# Generated by Django 3.1.4 on 2021-06-07 07:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pricing", "0005_auto_20210524_0941"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="itemmarketdataevent",
            name="pricing_ite_price_l_dec037_idx",
        ),
        migrations.AddIndex(
            model_name="itemmarketdataevent",
            index=models.Index(
                fields=["price_list", "-time", "item"],
                name="pricing_ite_price_l_c8ffd1_idx",
            ),
        ),
    ]