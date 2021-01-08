# Generated by Django 3.1.2 on 2020-12-12 11:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0019_auto_20201212_0952"),
    ]

    operations = [
        migrations.AlterField(
            model_name="discorduser",
            name="voucher",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="current_vouches",
                to="users.discorduser",
            ),
        ),
    ]