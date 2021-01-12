# Generated by Django 3.1.4 on 2021-01-12 12:30

from django.db import connection, migrations

# pylint: disable=unused-argument
def apply_migration(apps, schema_editor):
    EggTransaction = apps.get_model("bank", "EggTransaction")
    replacements = [
        ("TamagoPapi#8004", "[HONK] TamagoPapi#8004"),
        ("Kungfu [GOOP] Sampson Stone#5526", "Kungfu Trader#5526"),
        ("wolfs", "wolfs#0162"),
    ]
    for b, a in replacements:
        print(f"Replacing {b} with {a}")
        EggTransaction.objects.filter(counterparty_discord_username=b).update(
            counterparty_discord_username=a
        )

    cursor = connection.cursor()
    cursor.execute(
        """UPDATE bank_eggtransaction b SET counterparty_id = a.id
                    from users_gooseuser a
                    where a.username = b.counterparty_discord_username"""
    )
    errors = EggTransaction.objects.filter(counterparty__isnull=True)
    print(errors.values("counterparty_discord_username", "counterparty").all())
    assert errors.count() == 0


# pylint: disable=unused-argument
def revert_migration(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("bank", "0003_auto_20210112_1230"),
    ]

    operations = [
        migrations.RunPython(apply_migration, revert_migration),
    ]
