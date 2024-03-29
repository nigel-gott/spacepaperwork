# Generated by Django 3.1.4 on 2021-05-15 15:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("venmo", "0006_transfermethod"),
    ]

    operations = [
        migrations.AddField(
            model_name="transfermethod",
            name="transfer_type",
            field=models.TextField(
                choices=[
                    ("virtual_currency", "Automatic Virtual Currency"),
                    ("contract", "Via In Game Contracts"),
                    ("generate_command", "Generates a command for the user to send"),
                    (
                        "auto_send_generate_command",
                        "Generates a command and automatically sends it to a discord channel",
                    ),
                ],
                default="generate_command",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="transfermethod",
            name="default",
            field=models.BooleanField(
                default=False, help_text="The default transfer method"
            ),
        ),
        migrations.AlterField(
            model_name="transfermethod",
            name="name",
            field=models.TextField(
                help_text="The name users will see when choosing a transfer method"
            ),
        ),
        migrations.AlterField(
            model_name="transfermethod",
            name="via_contract",
            field=models.BooleanField(
                default=False,
                help_text="Whether to transfer using in-game contracts instead",
            ),
        ),
        migrations.AlterField(
            model_name="transfermethod",
            name="virtual_currency",
            field=models.ForeignKey(
                blank=True,
                help_text="The virtual currency to perform an automatic transfer with",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="venmo.virtualcurrency",
            ),
        ),
    ]
