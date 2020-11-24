# Generated by Django 3.1.2 on 2020-11-24 16:47

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("contracts", "0001_initial"),
        ("core", "0001_initial"),
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="contract",
            name="from_user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="my_contracts",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="contract",
            name="system",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="core.system"
            ),
        ),
        migrations.AddField(
            model_name="contract",
            name="to_char",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="users.character"
            ),
        ),
    ]
