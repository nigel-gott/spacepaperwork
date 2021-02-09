# Generated by Django 3.1.4 on 2021-02-09 08:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("user_forms", "0004_auto_20210208_2131"),
    ]

    operations = [
        migrations.CreateModel(
            name="FormQuestion",
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
                (
                    "question_type",
                    models.TextField(
                        choices=[
                            ("text", "text"),
                            ("number", "number"),
                            ("textarea", "large text area"),
                        ],
                        default="text",
                    ),
                ),
                ("question_title", models.TextField()),
                ("question_help_text", models.TextField(blank=True, null=True)),
                ("is_required", models.TextField(blank=True, null=True)),
                (
                    "form",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="user_forms.dynamicform",
                    ),
                ),
            ],
        ),
        migrations.RemoveField(
            model_name="signupquestionchoice",
            name="discord_role_given_from_choice",
        ),
        migrations.RemoveField(
            model_name="signupquestionchoice",
            name="signup_question",
        ),
        migrations.DeleteModel(
            name="SignUpQuestion",
        ),
        migrations.DeleteModel(
            name="SignUpQuestionChoice",
        ),
    ]
