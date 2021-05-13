# Generated by Django 3.1.4 on 2021-05-03 12:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0011_auto_20210503_1201"),
        ("items", "0008_auto_20210503_0928"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="itemchangeproposal",
            name="volume",
        ),
        migrations.AddField(
            model_name="itemchangeproposal",
            name="approved_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="itemchangeproposal",
            name="approved_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="item_change_approvals",
                to="users.gooseuser",
            ),
        ),
        migrations.AddField(
            model_name="itemchangeproposal",
            name="item_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="items.itemsubsubtype",
            ),
        ),
        migrations.AddField(
            model_name="itemchangeproposal",
            name="proposed_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="itemchangeproposal",
            name="proposed_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="item_change_proposals",
                to="users.gooseuser",
            ),
        ),
        migrations.AddField(
            model_name="itemchangeproposal",
            name="proposed_by_process",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="item",
            name="name",
            field=models.TextField(unique=True),
        ),
        migrations.AlterField(
            model_name="itemchangeproposal",
            name="change",
            field=models.TextField(
                choices=[
                    ("update", "update"),
                    ("delete", "delete"),
                    ("create", "create"),
                ]
            ),
        ),
    ]
