# Generated by Django 3.1.4 on 2021-02-08 14:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("users", "0019_auto_20210208_1113"),
    ]

    operations = [
        migrations.CreateModel(
            name="DynamicForm",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.TextField(blank=True, null=True)),
                ("header_text", models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="SignUpQuestion",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("question_name", models.TextField()),
                ("question_help_text", models.TextField(blank=True, null=True)),
                (
                    "question_type",
                    models.TextField(
                        choices=[
                            ("text", "text"),
                            ("number", "number"),
                            ("textarea", "large text area"),
                            ("multichoice_dropdown", "multiple choice dropdown"),
                        ]
                    ),
                ),
                (
                    "form",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="user_forms.dynamicform",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="SignUpQuestionChoice",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("choice", models.TextField()),
                (
                    "discord_role_given_from_choice",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="users.discordrole",
                    ),
                ),
                (
                    "signup_question",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="user_forms.signupquestion",
                    ),
                ),
            ],
        ),
    ]