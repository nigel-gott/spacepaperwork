from django import forms
from django.forms.models import ModelForm, inlineformset_factory

from goosetools.user_forms.models import DynamicForm, FormQuestion


class FormQuestionForm(ModelForm):
    is_required = forms.BooleanField(
        label="Question is Manditory", widget=forms.CheckboxInput(), required=False
    )

    class Meta:
        model = FormQuestion
        fields = "__all__"


FormQuestionFormSet = inlineformset_factory(
    DynamicForm, FormQuestion, form=FormQuestionForm, extra=1
)


class GeneratedForm(forms.Form):
    def __init__(self, dynamic_form: DynamicForm, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dynamic_form = dynamic_form
        questions = dynamic_form.formquestion_set.all()
        for question in questions:
            field_name = f"question_{question.id}"
            self.fields[field_name] = forms.CharField(
                required=question.is_required,  # type: ignore
                label=question.title,
                help_text=question.help_text or "",
            )
            self.initial[field_name] = ""

    def as_dict(self):
        answers = {}
        questions = self.dynamic_form.formquestion_set.all()
        for question in questions:
            field_name = f"question_{question.id}"
            if field_name in self.cleaned_data:
                answers[question.title] = self.cleaned_data[field_name]
        return answers
