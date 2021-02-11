from django.db import models
from django.urls import reverse


class DynamicForm(models.Model):
    title = models.TextField()
    description = models.TextField(null=True, blank=True)

    def get_absolute_url(self):
        return reverse("user_forms:form-detail", kwargs={"pk": self.pk})

    def __str__(self) -> str:
        return self.title


class FormQuestion(models.Model):
    form = models.ForeignKey(DynamicForm, on_delete=models.CASCADE)
    question_type = models.TextField(
        choices=[
            ("text", "text"),
        ],
        default="text",
    )
    title = models.TextField()
    help_text = models.TextField(null=True, blank=True)
    is_required = models.BooleanField(default=True)
