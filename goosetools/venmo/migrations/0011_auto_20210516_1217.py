# Generated by Django 3.1.4 on 2021-05-16 12:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("venmo", "0010_auto_20210516_1134"),
    ]

    operations = [
        migrations.AlterField(
            model_name="transfermethod",
            name="deposit_command_format",
            field=models.TextField(
                blank=True,
                help_text="This is the template used to generate an initial 'deposit' command the user should send before doing the transfer. If you include anyof the following pieces of text they will be replaced with their corresponding value when a command is generated: TRANSFERRING_DISCORD_USER, TOTAL_TRANSFER_AMOUNT",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="transfermethod",
            name="transfer_postfix_command_format",
            field=models.TextField(
                blank=True,
                help_text="This is the template used to generate the end of a 'transfer' command the user should send to actually perform the transfer. If you include any of the following pieces of text they will be replaced with their corresponding value when a command is generated: TRANSFERRING_DISCORD_USER, TOTAL_TRANSFER_AMOUNT",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="transfermethod",
            name="transfer_prefix_command_format",
            field=models.TextField(
                blank=True,
                help_text="This is the template used to generate the start of a 'transfer' command the user should send to actually perform the transfer. If you include any of the following pieces of text they will be replaced with their corresponding value when a command is generated: TRANSFERRING_DISCORD_USER, TOTAL_TRANSFER_AMOUNT",
                null=True,
            ),
        ),
    ]